"""Tools for the campaign brief agent to save campaign information."""
import json
from typing import Optional, Dict, Any
from types import SimpleNamespace
from google.adk.tools import FunctionTool
from agents.session_context import set_context as set_shared_context, get_context as get_shared_context
from agents.utils.session_helpers import normalize_session


def set_session_context(session_manager: Any, session_id: str, user_id: str) -> None:
    """Set the session context for the campaign brief agent tools."""
    set_shared_context("campaign_brief_agent", session_manager, session_id, user_id)


def _build_brief_payload(**kwargs: Any) -> Dict[str, Any]:
    """Normalize campaign brief payload, dropping empty fields."""
    return {k: v for k, v in kwargs.items() if v not in (None, "", [])}


def save_campaign_brief_tool(
    goal: str,
    platform: str = "any",
    location: Optional[str] = None,
    niche: Optional[str] = None,
    budget_per_creator: Optional[float] = None,
    num_creators: int = 1,
    business_name: Optional[str] = None,
    product_info: Optional[str] = None,
    audience_demographics: Optional[str] = None,
    audience_interests: Optional[str] = None
) -> str:
    """Save campaign brief information to the database and session.

    Persists the brief linked to the current session and user, and stores it in
    session memory for downstream agents (creator finder, outreach).
    """
    # Prefer the shared session context for consistency across agents
    shared_ctx = get_shared_context("shared")
    agent_ctx = get_shared_context("campaign_brief_agent")
    ctx = shared_ctx or agent_ctx
    if not ctx:
        return json.dumps({"success": False, "error": "Session context not available"})

    session_manager = ctx.get("session_manager")
    raw_session = SimpleNamespace(id=ctx.get("session_id"), user_id=ctx.get("user_id"), app_name=ctx.get("app_name"))
    try:
        norm = normalize_session(raw_session)
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})

    session_id = norm["session_id"]
    user_id = norm["user_id"]
    if not session_manager or not session_id:
        return json.dumps({"success": False, "error": "Session context incomplete"})

    session_memory = session_manager.get_session_memory(session_id)
    if not session_memory:
        return json.dumps({"success": False, "error": "Session not found"})

    brief = _build_brief_payload(
        goal=goal,
        platform=platform,
        location=location,
        niche=niche,
        budget_per_creator=budget_per_creator,
        num_creators=num_creators,
        business_name=business_name,
        product_info=product_info,
        audience_demographics=audience_demographics,
        audience_interests=audience_interests,
        session_id=session_id,
        user_id=user_id,
    )

    try:
        print(f"[CAMPAIGN_BRIEF] Starting tool execution for session {session_id}")
        from utils.message_utils import save_campaign_brief as save_brief_util

        print(f"[CAMPAIGN_BRIEF] Calling save_brief_util...")
        save_brief_util(user_id, session_id, brief)
        print(f"[CAMPAIGN_BRIEF] Brief saved to database")
        
        # Also keep in session memory for quick access by other agents
        print(f"[CAMPAIGN_BRIEF] Updating agent context...")
        session_memory.update_agent_context("campaign_brief_agent", "brief", brief)
        print(f"[CAMPAIGN_BRIEF] Agent context updated")
        
        # Transition to creator_finder stage after brief is saved
        print(f"[CAMPAIGN_BRIEF] About to transition stage...")
        from workflow_enums import WorkflowStage
        print(f"[CAMPAIGN_BRIEF] WorkflowStage imported: {WorkflowStage.CREATOR_FINDER}")
        session_memory.set_workflow_stage(WorkflowStage.CREATOR_FINDER)
        print(f"[CAMPAIGN_BRIEF] Stage transition complete. New stage: {session_memory.get_workflow_stage()}")
        
        return json.dumps({"success": True, "message": "Campaign brief saved successfully!", "brief": brief})
    except Exception as e:
        print(f"[TOOL ERROR] Failed to save campaign brief: {e}")
        import traceback
        traceback.print_exc()
        return json.dumps({"success": False, "error": str(e)})


save_campaign_brief = FunctionTool(save_campaign_brief_tool)
