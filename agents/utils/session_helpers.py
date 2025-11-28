"""Helpers for extracting and normalizing session metadata safely."""
from typing import Any, Dict


def normalize_session(session: Any) -> Dict[str, str]:
    """Return a normalized session dict with required fields.

    Expects a session-like object with `id` or `session_id` and `user_id`.
    Raises ValueError if missing.
    """
    if session is None:
        raise ValueError("Session object is missing")

    session_id = getattr(session, "id", None) or getattr(session, "session_id", None)
    user_id = getattr(session, "user_id", None)
    app_name = getattr(session, "app_name", "agents")

    if not session_id or not user_id:
        raise ValueError("Missing session_id or user_id in session")

    return {"session_id": session_id, "user_id": user_id, "app_name": app_name}
