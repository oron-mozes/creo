from typing import Any, Callable, Optional, Tuple

ANON_PREFIX = "anon_"


def is_authenticated_user(user_id: Optional[str]) -> bool:
    """Return True if the user_id represents an authenticated user."""
    if not user_id:
        return False
    return not str(user_id).startswith(ANON_PREFIX)


def resolve_user(token: Optional[str], anon_user_id: Optional[str], sid: str, verify_token: Callable[[str], Any]) -> Tuple[str, Optional[dict], bool]:
    """
    Resolve user identity from token or fallback to anonymous.

    Returns: (user_id, user_profile, is_authenticated)
    """
    user_id = None
    user_profile = None
    is_authenticated = False

    if token:
        payload = verify_token(token)
        if payload:
            user_id = payload.get("sub")
            user_profile = {"name": payload.get("name")}
            is_authenticated = is_authenticated_user(user_id)
            print(f"[AUTH] Authenticated user: {user_id}")
        else:
            print("[AUTH] WARNING: Invalid token provided, treating as anonymous")

    if not user_id:
        user_id = anon_user_id or f"anon_{sid[:12]}"
        print(f"[AUTH] Anonymous user: {user_id}")
        is_authenticated = False

    return user_id, user_profile, is_authenticated
