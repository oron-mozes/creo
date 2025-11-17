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

# Configuration
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
SECRET_KEY = os.getenv("SESSION_SECRET_KEY", "development-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

# Determine redirect URI based on environment
if os.getenv('K_SERVICE'):  # Cloud Run
    REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "https://your-app.run.app/api/auth/google/callback")
else:  # Local development
    REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/api/auth/google/callback")

# OAuth setup
oauth = OAuth()

if GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET:
    oauth.register(
        name='google',
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={
            'scope': 'openid email profile'
        }
    )

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

def verify_token(token: str) -> Optional[dict]:
    """Verify and decode a JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> UserInfo:
    """Dependency to get current authenticated user from JWT token."""
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")

    token = credentials.credentials
    payload = verify_token(token)

    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user_id = payload.get("sub")
    email = payload.get("email")
    name = payload.get("name")
    picture = payload.get("picture")

    if not user_id or not email:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    return UserInfo(user_id=user_id, email=email, name=name, picture=picture)

async def get_optional_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Optional[UserInfo]:
    """Dependency to get current user if authenticated, None otherwise."""
    if not credentials:
        return None

    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None

# Routes
@router.get("/login/google")
async def google_login(request: Request):
    """Initiate Google OAuth login flow."""
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
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
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
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

        # Redirect to frontend with token in URL fragment (for SPA)
        # Frontend will extract token and store it
        return RedirectResponse(
            url=f"{return_url}#access_token={access_token}",
            status_code=303
        )

    except Exception as e:
        print(f"[AUTH] Error in Google callback: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Authentication failed: {str(e)}")

@router.post("/logout")
async def logout(current_user: UserInfo = Depends(get_current_user)):
    """Logout user (client should delete token)."""
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
async def dev_login(email: str = "dev@example.com", name: str = "Dev User"):
    """Development-only endpoint to create a test user token."""
    if os.getenv('K_SERVICE'):
        raise HTTPException(status_code=404, detail="Not available in production")

    user_id = f"dev_{email.split('@')[0]}"

    access_token = create_access_token(
        data={
            "sub": user_id,
            "email": email,
            "name": name,
            "picture": None
        }
    )

    return TokenResponse(
        access_token=access_token,
        user=UserInfo(
            user_id=user_id,
            email=email,
            name=name,
            picture=None
        )
    )
