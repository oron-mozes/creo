"""Routing tools for the orchestrator agent."""
import logging
from pathlib import Path
import importlib.util
import json
import asyncio
from dataclasses import dataclass
from typing import Any, AsyncIterator, Optional, Dict
from collections.abc import AsyncIterable, Iterable

from google.adk.agents.llm_agent import Agent
from google.adk.tools.function_tool import FunctionTool
from google.adk.tools.tool_context import ToolContext
from google.genai import types

from agents.utils import AgentName
from agents.utils.frontdesk_payload import build_frontdesk_payload, to_frontdesk_string
from agents.utils.session_helpers import normalize_session
from workflow_enums import WorkflowStage
from session_manager import get_session_manager, SessionMemory

logger = logging.getLogger(__name__)

_AGENTS_DIR = Path(__file__).resolve().parent.parent

# Map agents to workflow stages for state tracking
_AGENT_STAGE_MAP = {
    AgentName.ONBOARDING_AGENT: WorkflowStage.ONBOARDING,
    AgentName.CAMPAIGN_BRIEF_AGENT: WorkflowStage.CAMPAIGN_BRIEF,
    AgentName.CREATOR_FINDER_AGENT: WorkflowStage.CREATOR_FINDER,
    AgentName.OUTREACH_MESSAGE_AGENT: WorkflowStage.OUTREACH_MESSAGE,
    AgentName.CAMPAIGN_BUILDER_AGENT: WorkflowStage.CAMPAIGN_BUILDER,
}


@dataclass
class AgentRunResult:
    """Result of running a sub-agent."""
    text: str
    event_count: int
    part_count: int
    text_event_count: int
    stage_before: str
    stage_after: str
    card_before: bool
    card_after: bool
    
    @property
    def state_changed(self) -> bool:
        """Check if session state changed."""
        return (
            self.stage_before != self.stage_after 
            or self.card_before != self.card_after
        )
    
    def log_summary(self, agent_name: str) -> None:
        """Log execution summary."""
        logger.info(
            f"{agent_name} completed: events={self.event_count}, "
            f"parts={self.part_count}, text_events={self.text_event_count}, "
            f"response_len={len(self.text)}"
        )
        
        if self.state_changed:
            logger.info(
                f"Session state changed: stage {self.stage_before} -> {self.stage_after}, "
                f"card {self.card_before} -> {self.card_after}"
            )


class SessionContext:
    """Helper to safely access session data from ToolContext."""
    
    def __init__(self, tool_context: ToolContext):
        self.tool_context = tool_context
        self._session_memory: Optional[SessionMemory] = None
        
    @property
    def session_memory(self) -> Optional[SessionMemory]:
        """Lazy load session memory."""
        if self._session_memory is not None:
            return self._session_memory
            
        try:
            session = getattr(self.tool_context, "session", None)
            if session is None:
                logger.warning("No session found in tool context")
                return None

            # Normalize with the shared helper to avoid field mismatches.
            norm = normalize_session(session)
            session_id = norm["session_id"]

            session_manager = get_session_manager()
            session_memory = session_manager.get_session_memory(session_id)
            if session_memory is None:
                # Ensure session exists and create memory if missing (should be rare).
                session_manager.ensure_session(
                    user_id=norm["user_id"], session_id=session_id
                )
                session_memory = session_manager.get_session_memory(session_id)

            self._session_memory = session_memory
            return self._session_memory
        except AttributeError as e:
            logger.error(f"Missing attribute when accessing session: {e}")
            return None
        except ValueError as e:
            logger.error(f"Failed to normalize session: {e}")
            return None
            
    def get_workflow_stage(self) -> Optional[WorkflowStage]:
        """Get current workflow stage."""
        if self.session_memory is None:
            return None
        return self.session_memory.get_workflow_stage()
        
    def set_workflow_stage(self, stage: WorkflowStage) -> bool:
        """Set workflow stage. Returns success."""
        if self.session_memory is None:
            logger.warning(f"Cannot set workflow stage to {stage.value}: no session; creating memory if possible")
            # Try to force-initialize memory if session exists.
            _ = self.session_memory
            if self._session_memory is None:
                return False
        self.session_memory.set_workflow_stage(stage)
        logger.info(f"Workflow stage set to {stage.value}")
        return True
        
    def has_business_card(self) -> bool:
        """Check if business card exists."""
        if self.session_memory is None:
            return False
        return self.session_memory.has_business_card()
    
    def set_frontdesk_called(self, value: bool) -> None:
        """Flag whether frontdesk has been called for the current turn."""
        if self.session_memory is None:
            return
        metadata = self.session_memory.get_shared_context().setdefault("metadata", {})
        metadata["frontdesk_called"] = value
    
    def snapshot_state(self) -> tuple[str, bool]:
        """Capture a snapshot of the workflow stage and business card presence."""
        stage = self.get_workflow_stage()
        stage_val = stage.value if stage else "unknown"
        has_card = self.has_business_card()
        return (stage_val, has_card)


def _load_agent(agent_enum: AgentName) -> Agent:
    """Import an agent module dynamically and return the Agent instance."""
    agent_name = agent_enum.value
    agent_dir = agent_name
    agent_path = _AGENTS_DIR / agent_dir / "agent.py"
    
    if not agent_path.exists():
        raise FileNotFoundError(
            f"Agent file not found: {agent_path}\n"
            f"Expected structure: agents/{agent_dir}/agent.py"
        )
    
    spec = importlib.util.spec_from_file_location(agent_name, agent_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(
            f"Unable to load agent spec for {agent_name} from {agent_path}"
        )
    
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    attr_name = "frontdesk" if agent_enum == AgentName.FRONTDESK_AGENT else agent_name
    
    if not hasattr(module, attr_name):
        raise AttributeError(
            f"Agent module {agent_path} missing expected attribute '{attr_name}'"
        )
    
    agent = getattr(module, attr_name)
    if not isinstance(agent, Agent):
        raise TypeError(
            f"Expected Agent instance, got {type(agent)} for {attr_name}"
        )
    
    return agent


# Load all agents at module initialization
_sub_agents = {
    AgentName.ONBOARDING_AGENT: _load_agent(AgentName.ONBOARDING_AGENT),
    AgentName.CREATOR_FINDER_AGENT: _load_agent(AgentName.CREATOR_FINDER_AGENT),
    AgentName.CAMPAIGN_BRIEF_AGENT: _load_agent(AgentName.CAMPAIGN_BRIEF_AGENT),
    AgentName.OUTREACH_MESSAGE_AGENT: _load_agent(AgentName.OUTREACH_MESSAGE_AGENT),
    AgentName.CAMPAIGN_BUILDER_AGENT: _load_agent(AgentName.CAMPAIGN_BUILDER_AGENT),
    AgentName.FRONTDESK_AGENT: _load_agent(AgentName.FRONTDESK_AGENT),
}


def _normalize_request_text(request: Any) -> str:
    """Convert tool request payloads to a clean text string."""
    if request is None:
        return ""
    
    if isinstance(request, str):
        return request
    
    if isinstance(request, dict):
        if "request" in request:
            req_value = request.get("request")
            return str(req_value) if req_value is not None else ""
        return json.dumps(request, ensure_ascii=False, indent=2)
    
    return str(request)


async def _to_async_iter(obj: Any) -> AsyncIterator[Any]:
    """Convert various iterable types to async iterator."""
    if isinstance(obj, AsyncIterable):
        async for item in obj:
            yield item
    elif asyncio.iscoroutine(obj):
        result = await obj
        # Handle the awaited result
        if isinstance(result, (AsyncIterable, Iterable)):
            async for item in _to_async_iter(result):
                yield item
        else:
            yield result
    elif isinstance(obj, Iterable) and not isinstance(obj, (str, bytes)):
        for item in obj:
            yield item
    else:
        yield obj


async def _run_agent_and_get_text(
    agent: Agent, 
    tool_context: ToolContext, 
    request: str
) -> str:
    """
    Run an agent and collect its text response.
    
    Args:
        agent: The agent to run
        tool_context: Context containing session information
        request: User request text
        
    Returns:
        Concatenated text response from agent
        
    Raises:
        RuntimeError: If agent execution fails critically
    """
    ctx = SessionContext(tool_context)
    before_stage, before_card = ctx.snapshot_state()
    
    session = getattr(tool_context, "session", None)
    norm = normalize_session(session)
    session_id = norm["session_id"]
    user_id = norm["user_id"]
    app_name = norm["app_name"]

    # Normalize request
    if isinstance(request, dict) and "request" in request:
        request = request["request"]

    # Use existing runner so we keep the real session store.
    # Use session_manager to create a sub-runner for the specific agent
    # This ensures we run the sub-agent (not root_agent) while sharing the session service
    session_manager = getattr(tool_context, "session_manager", None)
    if session_manager is None:
        raise RuntimeError("Missing session_manager in tool context")
        
    runner = session_manager.create_sub_runner(agent, user_id)
    session_service = runner.session_service
    if session_service is None:
        raise RuntimeError("Sub-runner has no session_service")
    
    # Create message, optionally augmenting with business card to reduce LLM misses
    message_text = request
    if agent.name == AgentName.CAMPAIGN_BRIEF_AGENT.value and ctx.has_business_card():
        card_data = ctx.session_memory.get_business_card() if ctx.session_memory else {}
        message_text = (
            "Note: Business card is already saved. "
            f"Business card: {card_data}. "
            f"User request: {request}"
        )

    new_message = types.Content(role="user", parts=[types.Part(text=message_text)])
    
    # Ensure the runner has the existing session; do NOT create new sessions here.
    existing_session = await session_service.get_session(
        app_name=app_name,
        user_id=user_id,
        session_id=session_id,
    )
    if existing_session is None:
        raise RuntimeError(
            f"Session not found for {session_id}; orchestrator should receive an existing session"
        )
    
    # Run agent
    agent_response = runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=new_message,
    )

    # Collect response
    response_chunks: list[str] = []
    event_count = 0
    part_count = 0
    text_event_count = 0

    try:
        async for event in _to_async_iter(agent_response):
            # Skip non-event payloads
            if not hasattr(event, "parts") and not hasattr(event, "content"):
                continue
                
            event_count += 1
            
            # Extract parts
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
                        logger.debug(f"Added text chunk: {part.text[:80]}...")
    
    except Exception as e:
        logger.error(f"Error during agent execution: {e}")
        raise RuntimeError(f"Agent {agent.name} execution failed: {e}") from e

    # Build result
    result = AgentRunResult(
        text="".join(response_chunks),
        event_count=event_count,
        part_count=part_count,
        text_event_count=text_event_count,
        stage_before=before_stage,
        stage_after=ctx.snapshot_state()[0],
        card_before=before_card,
        card_after=ctx.has_business_card(),
    )

    # If onboarding produced no text but a business card now exists,
    # emit a confirmation and advance to campaign brief stage.
    if ctx.has_business_card():
        ctx.set_workflow_stage(WorkflowStage.CAMPAIGN_BRIEF)

        if not response_chunks:
            card_data: Dict[str, Any] = {}
            if ctx.session_memory:
                existing_card = ctx.session_memory.get_business_card()
                if existing_card:
                    card_data = existing_card
            name = card_data.get("name") or "your business"
            default_msg = (
                f"Thanks for confirming the details for {name}. I've saved your business card. "
                "Let's move on to planning your campaign."
            )
            result.text = default_msg
            response_chunks.append(default_msg)
    
    result.log_summary(agent.name)
    return result.text


# ============================================================================
# Routing Tool Functions
# ============================================================================

@FunctionTool
async def route_to_onboarding_agent(request: str, tool_context: ToolContext) -> str:
    """Route to onboarding agent for collecting business information."""
    ctx = SessionContext(tool_context)
    ctx.set_frontdesk_called(False)
    ctx.set_workflow_stage(WorkflowStage.ONBOARDING)
    return await _run_agent_and_get_text(
        _sub_agents[AgentName.ONBOARDING_AGENT], 
        tool_context, 
        request
    )


@FunctionTool
async def route_to_creator_finder_agent(request: str, tool_context: ToolContext) -> str:
    """Route to creator finder agent for searching influencers/creators."""
    ctx = SessionContext(tool_context)
    ctx.set_frontdesk_called(False)
    ctx.set_workflow_stage(WorkflowStage.CREATOR_FINDER)
    return await _run_agent_and_get_text(
        _sub_agents[AgentName.CREATOR_FINDER_AGENT], 
        tool_context, 
        request
    )


@FunctionTool
async def route_to_campaign_brief_agent(request: str, tool_context: ToolContext) -> str:
    """Route to campaign brief agent for planning marketing campaigns."""
    ctx = SessionContext(tool_context)
    ctx.set_frontdesk_called(False)
    ctx.set_workflow_stage(WorkflowStage.CAMPAIGN_BRIEF)
    return await _run_agent_and_get_text(
        _sub_agents[AgentName.CAMPAIGN_BRIEF_AGENT], 
        tool_context, 
        request
    )


@FunctionTool
async def route_to_outreach_message_agent(request: str, tool_context: ToolContext) -> str:
    """Route to outreach message agent for creating influencer outreach messages."""
    ctx = SessionContext(tool_context)
    ctx.set_frontdesk_called(False)
    ctx.set_workflow_stage(WorkflowStage.OUTREACH_MESSAGE)
    return await _run_agent_and_get_text(
        _sub_agents[AgentName.OUTREACH_MESSAGE_AGENT], 
        tool_context, 
        request
    )


@FunctionTool
async def route_to_campaign_builder_agent(request: str, tool_context: ToolContext) -> str:
    """Route to campaign builder agent for assembling complete campaigns."""
    ctx = SessionContext(tool_context)
    ctx.set_frontdesk_called(False)
    ctx.set_workflow_stage(WorkflowStage.CAMPAIGN_BUILDER)
    return await _run_agent_and_get_text(
        _sub_agents[AgentName.CAMPAIGN_BUILDER_AGENT], 
        tool_context, 
        request
    )


@FunctionTool
async def route_to_frontdesk_agent(request: str, tool_context: ToolContext) -> str:
    """Route to frontdesk agent for formatting responses for end users."""
    ctx = SessionContext(tool_context)
    ctx.set_frontdesk_called(True)
    
    specialist_text = _normalize_request_text(request)
    
    stage = ctx.get_workflow_stage()
    stage_text = stage.value if stage else "unspecified stage"
    
    # Get last user message
    last_user = ""
    if ctx.session_memory:
        messages = ctx.session_memory.get_shared_context().get("messages", [])
        for msg in reversed(messages):
            if msg.get("role") == "user":
                last_user = str(msg.get("content", "")).strip()
                break

    payload = build_frontdesk_payload(
        stage=stage_text,
        user_request=last_user,
        specialist_response=specialist_text,
    )

    response = await _run_agent_and_get_text(
        _sub_agents[AgentName.FRONTDESK_AGENT], 
        tool_context, 
        to_frontdesk_string(payload)
    )
    
    # Save response to metadata for fallback in case Orchestrator fails to echo it
    if ctx.session_memory:
        metadata = ctx.session_memory.get_shared_context().setdefault("metadata", {})
        metadata["last_frontdesk_response"] = response
        
    return response


async def _set_workflow_stage_fn(stage: str, tool_context: ToolContext) -> dict[str, Any]:
    """Explicitly set the workflow stage in session memory."""
    ctx = SessionContext(tool_context)
    
    if ctx.session_memory is None:
        return {"success": False, "error": "No session found; unable to set workflow stage."}

    try:
        target_stage = WorkflowStage(stage)
    except ValueError:
        return {"success": False, "error": f"Invalid workflow stage: {stage}"}

    if ctx.set_workflow_stage(target_stage):
        return {"success": True, "message": f"Workflow stage set to {target_stage.value}"}
    else:
        return {"success": False, "error": "Failed to set workflow stage"}


set_workflow_stage_tool = FunctionTool(_set_workflow_stage_fn)


# Export all routing tools
routing_tools = [
    route_to_onboarding_agent,
    route_to_creator_finder_agent,
    route_to_campaign_brief_agent,
    route_to_outreach_message_agent,
    route_to_campaign_builder_agent,
    route_to_frontdesk_agent,
    set_workflow_stage_tool,
]
