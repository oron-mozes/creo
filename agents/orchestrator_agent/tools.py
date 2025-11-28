"""Routing tools for the orchestrator agent."""
from pathlib import Path
import importlib.util
import json
import uuid
import asyncio
from typing import Any, Dict, AsyncIterator, Iterable, Optional, cast

from google.adk.agents.llm_agent import Agent
from google.adk.tools.function_tool import FunctionTool
from google.adk.tools.tool_context import ToolContext
from google.adk.runners import InMemoryRunner, Runner
from google.genai import types
from google.genai.types import Tool, ToolConfig, FunctionCallingConfig, FunctionCallingConfigMode

from agents.utils import AgentName
from agents.utils.frontdesk_payload import build_frontdesk_payload, to_frontdesk_string
from agents.utils.session_helpers import normalize_session
from workflow_enums import WorkflowStage
from session_manager import get_session_manager

_AGENTS_DIR = Path(__file__).resolve().parent.parent

# Map agents to workflow stages for state tracking
_AGENT_STAGE_MAP = {
    AgentName.ONBOARDING_AGENT: WorkflowStage.ONBOARDING,
    AgentName.CAMPAIGN_BRIEF_AGENT: WorkflowStage.CAMPAIGN_BRIEF,
    AgentName.CREATOR_FINDER_AGENT: WorkflowStage.CREATOR_FINDER,
    AgentName.OUTREACH_MESSAGE_AGENT: WorkflowStage.OUTREACH_MESSAGE,
    AgentName.CAMPAIGN_BUILDER_AGENT: WorkflowStage.CAMPAIGN_BUILDER,
}


def _load_agent(agent_enum: AgentName) -> Agent:
    """Import an agent module dynamically and return the Agent instance."""
    agent_name = agent_enum.value
    agent_dir = agent_name
    agent_path = _AGENTS_DIR / agent_dir / "agent.py"
    spec = importlib.util.spec_from_file_location(agent_name, agent_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load agent spec for {agent_name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    if agent_enum == AgentName.FRONTDESK_AGENT:
        return cast(Agent, getattr(module, "frontdesk"))
    return cast(Agent, getattr(module, agent_name))


_sub_agents = {
    AgentName.ONBOARDING_AGENT: _load_agent(AgentName.ONBOARDING_AGENT),
    AgentName.CREATOR_FINDER_AGENT: _load_agent(AgentName.CREATOR_FINDER_AGENT),
    AgentName.CAMPAIGN_BRIEF_AGENT: _load_agent(AgentName.CAMPAIGN_BRIEF_AGENT),
    AgentName.OUTREACH_MESSAGE_AGENT: _load_agent(AgentName.OUTREACH_MESSAGE_AGENT),
    AgentName.CAMPAIGN_BUILDER_AGENT: _load_agent(AgentName.CAMPAIGN_BUILDER_AGENT),
    AgentName.FRONTDESK_AGENT: _load_agent(AgentName.FRONTDESK_AGENT),
}


def _get_session_memory_from_context(tool_context: ToolContext) -> Any:
    """Helper to retrieve SessionMemory using the session_id in ToolContext."""
    try:
        session = getattr(tool_context, "session", None)
        session_id = getattr(session, "session_id", None) if session else None
        if not session_id:
            return None
        session_manager = get_session_manager()
        return session_manager.get_session_memory(session_id)
    except Exception as e:
        print(f"[ORCHESTRATOR] Failed to fetch session memory: {e}", flush=True)
        return None


def _snapshot_session_state(tool_context: ToolContext) -> tuple[str, bool]:
    """Capture a snapshot of the workflow stage and business card presence."""
    session_memory = _get_session_memory_from_context(tool_context)
    if not session_memory:
        return ("unknown", False)
    stage = session_memory.get_workflow_stage()
    stage_val = stage.value if stage else "None"
    has_card = session_memory.has_business_card()
    return (stage_val, has_card)


def _normalize_request_text(request: Any) -> str:
    """Convert tool request payloads to a clean text string."""
    if request is None:
        return ""
    if isinstance(request, dict):
        if "request" in request:
            return str(request.get("request") or "")
        return json.dumps(request, ensure_ascii=False)
    return str(request)


def _set_frontdesk_called(tool_context: ToolContext, value: bool) -> None:
    """Flag whether frontdesk has been called for the current turn."""
    session_memory = _get_session_memory_from_context(tool_context)
    if not session_memory:
        return
    metadata = session_memory.get_shared_context().setdefault("metadata", {})
    metadata["frontdesk_called"] = value


def _set_workflow_stage(agent_enum: AgentName, tool_context: ToolContext) -> None:
    """Persist the current workflow stage in session memory based on the routed agent."""
    try:
        session = getattr(tool_context, "session", None)
        session_id = getattr(session, "session_id", None) if session else None
        if not session_id:
            return

        session_manager = get_session_manager()
        session_memory = session_manager.get_session_memory(session_id)
        if not session_memory:
            return

        target_stage = _AGENT_STAGE_MAP.get(agent_enum)
        if not target_stage:
            return

        current_stage = session_memory.get_workflow_stage()
        if current_stage != target_stage:
            session_memory.set_workflow_stage(target_stage)
            print(
                f"[ORCHESTRATOR] Workflow stage set to {target_stage.value} for session {session_id}",
                flush=True,
            )
    except Exception as e:
        print(f"[ORCHESTRATOR] Failed to set workflow stage for {agent_enum.value}: {e}", flush=True)


async def _run_agent_and_get_text(agent: Agent, tool_context: ToolContext, request: str) -> str:
    """Helper to run an agent and collect its text response using a new runner with shared session."""
    response_chunks: list[str] = []
    before_stage, before_card = _snapshot_session_state(tool_context)

    session = getattr(tool_context, "session", None)
    norm = normalize_session(session)
    session_id = norm["session_id"]
    user_id = norm["user_id"]
    app_name = norm["app_name"]

    if isinstance(request, dict) and "request" in request:
        request = request["request"]

    runner: Runner = InMemoryRunner(app_name=app_name, agent=agent)
    # ToolContext doesn't expose runner attribute in type hints
    setattr(tool_context, "runner", runner)

    new_message = types.Content(role="user", parts=[types.Part(text=request)])
    agent_response = runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=new_message,
    )

    event_count = 0
    part_count = 0
    text_event_count = 0

    async def _to_async_iter(obj: Any) -> AsyncIterator[Any]:
        if hasattr(obj, "__aiter__"):
            async for item in obj:
                yield item
        elif asyncio.iscoroutine(obj):
            res = await obj
            async for item in _to_async_iter(res):
                yield item
        elif isinstance(obj, Iterable):
            for item in obj:
                yield item
        else:
            return

    async for event in _to_async_iter(agent_response):
        # Skip non-event payloads (e.g., stray strings)
        if not hasattr(event, "parts") and not hasattr(event, "content"):
            continue
        event_count += 1
        parts = getattr(event, "parts", None)
        if parts is None and hasattr(event, "content"):
            parts = getattr(event.content, "parts", []) or []
        else:
            parts = parts or []
        if parts:
            part_count += len(parts)
            for part in parts:
                if part.text:
                    text_event_count += 1
                    response_chunks.append(part.text)
                    print(f"[ORCHESTRATOR] Added text: {part.text[:80]}...", flush=True)

    print(
        f"[ORCHESTRATOR] Sub-agent {agent.name} completed: "
        f"events={event_count}, parts={part_count}, text_events={text_event_count}, "
        f"response_len={len(''.join(response_chunks))}",
        flush=True,
    )
    after_stage, after_card = _snapshot_session_state(tool_context)
    if (after_stage, after_card) != (before_stage, before_card):
        print(
            f"[ORCHESTRATOR] Session state changed after {agent.name}: "
            f"stage {before_stage} -> {after_stage}, "
                f"business_card {'yes' if before_card else 'no'} -> {'yes' if after_card else 'no'}",
                flush=True,
            )

    return "".join(response_chunks)


@FunctionTool
async def route_to_onboarding_agent(request: str, tool_context: ToolContext) -> str:
    """Route to onboarding agent for collecting business information."""
    _set_frontdesk_called(tool_context, False)
    _set_workflow_stage(AgentName.ONBOARDING_AGENT, tool_context)
    return await _run_agent_and_get_text(_sub_agents[AgentName.ONBOARDING_AGENT], tool_context, request)


@FunctionTool
async def route_to_creator_finder_agent(request: str, tool_context: ToolContext) -> str:
    """Route to creator finder agent for searching influencers/creators."""
    _set_frontdesk_called(tool_context, False)
    _set_workflow_stage(AgentName.CREATOR_FINDER_AGENT, tool_context)
    return await _run_agent_and_get_text(_sub_agents[AgentName.CREATOR_FINDER_AGENT], tool_context, request)


@FunctionTool
async def route_to_campaign_brief_agent(request: str, tool_context: ToolContext) -> str:
    """Route to campaign brief agent for planning marketing campaigns."""
    _set_frontdesk_called(tool_context, False)
    _set_workflow_stage(AgentName.CAMPAIGN_BRIEF_AGENT, tool_context)
    return await _run_agent_and_get_text(_sub_agents[AgentName.CAMPAIGN_BRIEF_AGENT], tool_context, request)


@FunctionTool
async def route_to_outreach_message_agent(request: str, tool_context: ToolContext) -> str:
    """Route to outreach message agent for creating influencer outreach messages."""
    _set_frontdesk_called(tool_context, False)
    _set_workflow_stage(AgentName.OUTREACH_MESSAGE_AGENT, tool_context)
    return await _run_agent_and_get_text(_sub_agents[AgentName.OUTREACH_MESSAGE_AGENT], tool_context, request)


@FunctionTool
async def route_to_campaign_builder_agent(request: str, tool_context: ToolContext) -> str:
    """Route to campaign builder agent for assembling complete campaigns."""
    _set_frontdesk_called(tool_context, False)
    _set_workflow_stage(AgentName.CAMPAIGN_BUILDER_AGENT, tool_context)
    return await _run_agent_and_get_text(_sub_agents[AgentName.CAMPAIGN_BUILDER_AGENT], tool_context, request)


@FunctionTool
async def route_to_frontdesk_agent(request: str, tool_context: ToolContext) -> str:
    """Route to frontdesk agent for formatting responses for end users."""
    _set_frontdesk_called(tool_context, True)
    specialist_text = _normalize_request_text(request)

    session_memory = _get_session_memory_from_context(tool_context)
    stage_text = "unspecified stage"
    last_user = ""
    if session_memory:
        stage = session_memory.get_workflow_stage()
        if stage:
            stage_text = stage.value
        messages = session_memory.get_shared_context().get("messages", [])
        last_user = next((m.get("content") for m in reversed(messages) if m.get("role") == "user"), "") or ""
        last_user = last_user.strip()

    payload = build_frontdesk_payload(
        stage=stage_text,
        user_request=last_user,
        specialist_response=specialist_text,
    )

    return await _run_agent_and_get_text(_sub_agents[AgentName.FRONTDESK_AGENT], tool_context, to_frontdesk_string(payload))


async def _set_workflow_stage_fn(stage: str, tool_context: ToolContext) -> Dict[str, Any]:
    """Explicitly set the workflow stage in session memory. Returns a dict."""
    session_memory = _get_session_memory_from_context(tool_context)
    if not session_memory:
        return {"success": False, "error": "No session found; unable to set workflow stage."}

    try:
        target_stage = WorkflowStage(stage)
    except Exception:
        return {"success": False, "error": f"Invalid workflow stage: {stage}"}

    session_memory.set_workflow_stage(target_stage)
    return {"success": True, "message": f"Workflow stage set to {target_stage.value}"}


set_workflow_stage_tool = FunctionTool(_set_workflow_stage_fn)


routing_tools = [
    route_to_onboarding_agent,
    route_to_creator_finder_agent,
    route_to_campaign_brief_agent,
    route_to_outreach_message_agent,
    route_to_campaign_builder_agent,
    route_to_frontdesk_agent,
    set_workflow_stage_tool,
]
