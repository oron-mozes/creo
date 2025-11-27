"""Authentication module for Google OAuth and JWT token management."""
from __future__ import annotations

import os
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, Request, Response
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from authlib.integrations.starlette_client import OAuth
from pydantic import BaseModel
import httpx
from db import get_db  # For persisting user records
from services.user_service import UserService

# Configuration
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
SECRET_KEY = os.getenv("SESSION_SECRET_KEY", "development-secret-key-change-in-production")
ALGORITHM = "HS256"
# Sliding-session window: 12 hours from last interaction
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 12
COOKIE_NAME = "creo_auth_token"
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "false").lower() == "true"
COOKIE_DOMAIN = os.getenv("COOKIE_DOMAIN")

# Determine redirect URI based on environment
if os.getenv('K_SERVICE'):  # Cloud Run
    REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "https://your-app.run.app/api/auth/google/callback")
else:  # Local development
    REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/api/auth/google/callback")

# OAuth setup
oauth = OAuth()
_user_service: Optional[UserService] = None
try:
    _user_service = UserService(get_db())
except Exception as e:  # pragma: no cover - local dev without Firestore
    print(f"[AUTH] UserService unavailable: {e}")

def google_config_present() -> bool:
    return bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET)


def log_google_config_state(prefix: str = "[AUTH]") -> None:
    """Log presence of Google OAuth env vars without leaking secrets."""
    print(
        f"{prefix} GOOGLE_CLIENT_ID set: {bool(GOOGLE_CLIENT_ID)}, "
        f"GOOGLE_CLIENT_SECRET set: {bool(GOOGLE_CLIENT_SECRET)}, "
        f"REDIRECT_URI: {REDIRECT_URI}",
        flush=True,
    )


if google_config_present():
    oauth.register(
        name='google',
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={
            'scope': 'openid email profile'
        }
    )
else:
    log_google_config_state()

# Security
security = HTTPBearer(auto_error=False)

# Router
router = APIRouter(prefix="/api/auth", tags=["authentication"])

# Models
class UserInfo(BaseModel):
    user_id: str
    email: str
    name: str
    picture: Optional[str] = None

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserInfo

# Helper functions
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def set_auth_cookie(response: Response, token: str):
    """Set the auth token in an HttpOnly cookie."""
    max_age = ACCESS_TOKEN_EXPIRE_MINUTES * 60
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="lax",
        max_age=max_age,
        expires=max_age,
        domain=COOKIE_DOMAIN or None,
        path="/",
    )


def clear_auth_cookie(response: Response):
    """Clear the auth token cookie."""
    response.delete_cookie(
        key=COOKIE_NAME,
        domain=COOKIE_DOMAIN or None,
        path="/",
    )

def verify_token(token: str) -> Optional[dict]:
    """Verify and decode a JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

def _refresh_cookie_if_needed(payload: dict, response: Response) -> None:
    """Refresh the auth cookie if the token is nearing expiry (sliding window)."""
    exp = payload.get("exp")
    if not exp:
        return

    # If less than 4 hours remaining, issue a fresh 12-hour token
    time_remaining = datetime.utcfromtimestamp(exp) - datetime.utcnow()
    if time_remaining.total_seconds() <= 4 * 60 * 60:
        refreshed_token = create_access_token(
            {
                "sub": payload.get("sub"),
                "email": payload.get("email"),
                "name": payload.get("name"),
                "picture": payload.get("picture"),
            }
        )
        set_auth_cookie(response, refreshed_token)


async def get_current_user(
    request: Request,
    response: Response,
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> UserInfo:
    """Dependency to get current authenticated user from JWT token or auth cookie."""
    token = credentials.credentials if credentials else None

    # Fall back to HttpOnly cookie if no bearer token was provided
    if not token:
        token = request.cookies.get(COOKIE_NAME)

    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    payload = verify_token(token)

    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user_id = payload.get("sub")
    email = payload.get("email")
    name = payload.get("name")
    picture = payload.get("picture")

    if not user_id or not email:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    # Sliding refresh to extend session on activity
    _refresh_cookie_if_needed(payload, response)

    return UserInfo(user_id=user_id, email=email, name=name, picture=picture)

async def get_optional_user(
    request: Request,
    response: Response,
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Optional[UserInfo]:
    """Dependency to get current user if authenticated, None otherwise."""
    try:
        return await get_current_user(request, response, credentials)
    except HTTPException:
        return None

# Routes
@router.get("/login/google")
async def google_login(request: Request):
    """Initiate Google OAuth login flow."""
    if not google_config_present():
        log_google_config_state()
        raise HTTPException(
            status_code=500,
            detail="Google OAuth not configured. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET environment variables."
        )

    # Store return URL in state parameter
    return_url = request.query_params.get("return_url", "/")
    redirect_uri = REDIRECT_URI

    # Generate authorization URL
    return await oauth.google.authorize_redirect(request, redirect_uri, state=return_url)

@router.get("/google/callback")
async def google_callback(request: Request):
    """Handle Google OAuth callback and create user session."""
    if not google_config_present():
        log_google_config_state()
        raise HTTPException(
            status_code=500,
            detail="Google OAuth not configured"
        )

    try:
        # Get access token from Google
        token = await oauth.google.authorize_access_token(request)

        # Get user info from Google
        user_info = token.get('userinfo')
        if not user_info:
            raise HTTPException(status_code=400, detail="Failed to get user info from Google")

        # Extract user data
        google_user_id = user_info.get('sub')
        email = user_info.get('email')
        name = user_info.get('name')
        picture = user_info.get('picture')

        if not google_user_id or not email:
            raise HTTPException(status_code=400, detail="Invalid user info from Google")

        # Create our user_id (prefixed with 'google_')
        user_id = f"google_{google_user_id}"

        # Persist/update user record in DB (if available)
        if _user_service:
            _user_service.ensure_user_record(
                creo_user_id=user_id,
                email=email,
                name=name,
                picture=picture,
            )

        # Create JWT token
        access_token = create_access_token(
            data={
                "sub": user_id,
                "email": email,
                "name": name,
                "picture": picture
            }
        )

        # Get return URL from state
        return_url = request.query_params.get("state", "/")

        # Redirect back to frontend and store token in HttpOnly cookie
        response = RedirectResponse(
            url=return_url,
            status_code=303
        )
        set_auth_cookie(response, access_token)
        return response

    except Exception as e:
        print(f"[AUTH] Error in Google callback: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Authentication failed: {str(e)}")

@router.post("/logout")
async def logout(response: Response, current_user: UserInfo = Depends(get_current_user)):
    """Logout user (clears HttpOnly auth cookie)."""
    clear_auth_cookie(response)
    return {"status": "success", "message": "Logged out successfully"}

@router.get("/me")
async def get_me(current_user: UserInfo = Depends(get_current_user)) -> UserInfo:
    """Get current authenticated user info."""
    return current_user

@router.get("/check")
async def check_auth(user: Optional[UserInfo] = Depends(get_optional_user)):
    """Check if user is authenticated."""
    if user:
        return {"authenticated": True, "user": user}
    return {"authenticated": False, "user": None}

# For development/testing: login with mock user
@router.post("/dev/login")
async def dev_login(
    response: Response,
    email: str = "dev@example.com",
    name: str = "Dev User"
):
    """Development-only endpoint to create a test user token."""
    if os.getenv('K_SERVICE'):
        raise HTTPException(status_code=404, detail="Not available in production")

    user_id = f"dev_{email.split('@')[0]}"

    if _user_service:
        _user_service.ensure_user_record(
            creo_user_id=user_id,
            email=email,
            name=name,
            picture=None,
        )

    access_token = create_access_token(
        data={
            "sub": user_id,
            "email": email,
            "name": name,
            "picture": None
        }
    )

    token_response = TokenResponse(
        access_token=access_token,
        user=UserInfo(
            user_id=user_id,
            email=email,
            name=name,
            picture=None
        )
    )

    # Set HttpOnly cookie for dev login
    set_auth_cookie(response, access_token)
    return token_response
