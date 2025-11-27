"""Auth gating tool for outreach agent."""
from typing import Optional
from google.adk.tools import FunctionTool


def require_auth_for_outreach_tool(reason: Optional[str] = None) -> str:
    """
    Signal the client that authentication is required before continuing outreach.

    The frontend should display a login widget when this is returned.
    """
    return reason or "Authentication required to send outreach emails. Please sign in to continue."


require_auth_for_outreach = FunctionTool(require_auth_for_outreach_tool)
