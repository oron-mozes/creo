"""Auth gating tool for outreach agent."""
from typing import Optional, Dict, Any
from google.adk.tools import FunctionTool

from agents.session_context import get_context
from sockets.utils.auth import is_authenticated_user


def _is_authenticated() -> bool:
    # Prefer shared context; fallback to outreach-specific if set
    ctx = get_context("shared") or get_context("outreach_message_agent")
    if not ctx:
        return False
    user_id = ctx.get("user_id")
    return is_authenticated_user(user_id)


def require_auth_for_outreach_tool(reason: Optional[str] = None) -> Dict[str, Any]:
    """
    Signal the client that authentication is required before continuing outreach.

    Returns a structured payload indicating whether auth is required.
    """
    authed = _is_authenticated()
    if authed:
        return {"success": True, "auth_required": False, "message": "Authenticated; outreach may proceed."}

    # Set flag in session metadata so run_agent can trigger login UI
    ctx = get_context("shared") or get_context("outreach_message_agent")
    if ctx and "session_manager" in ctx:
        session_manager = ctx["session_manager"]
        session_id = ctx.get("session_id")
        if session_manager and session_id:
            session_memory = session_manager.get_session_memory(session_id)
            if session_memory:
                metadata = session_memory.get_shared_context().setdefault("metadata", {})
                metadata["auth_required_triggered"] = True

    return {
        "success": False,
        "auth_required": True,
        "message": reason or "Authentication required to send outreach emails. Please sign in to continue.",
    }


require_auth_for_outreach = FunctionTool(require_auth_for_outreach_tool)
