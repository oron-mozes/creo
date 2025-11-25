"""Workflow Orchestrator agent for ADK web interface.

ARCHITECTURE NOTE - Context Preservation Fix:
============================================
This orchestrator uses a CUSTOM ROUTING APPROACH instead of AgentTool wrappers
to solve a critical ADK issue with tool calling reliability.

PROBLEM:
- AgentTool creates a fresh ExecutionContext for each sub-agent call
- This loses conversation history and workflow state (similar to losing REQUEST scope in NestJS)
- Agents cannot track multi-turn workflows or reliably decide when to call tools
- Documented in GitHub Issue #1746: https://github.com/google/adk/issues/1746

SOLUTION:
- Use FunctionTool wrappers for routing decisions (routing_tool)
- Invoke agents directly via agent.run_async() to preserve ExecutionContext
- Context preservation is like NestJS @Scope.REQUEST - shared across entire request tree

BENEFITS:
- Conversation history persists across agent calls
- Tools (like GoogleSearchTool) work reliably with context awareness
- Orchestrator remains an LLM-driven agent making intelligent routing decisions
- All agents can access shared request-scoped state

This approach maintains the orchestrator pattern while fixing the context isolation bug.
"""
from pathlib import Path
import importlib.util
import json
import uuid
from typing import Any
from google.adk.agents.llm_agent import Agent
from google.adk.tools.function_tool import FunctionTool
from google.adk.tools.tool_context import ToolContext
from google.adk.runners import InMemoryRunner, Runner
from google.genai import types
from google.genai.types import Tool, ToolConfig, FunctionCallingConfig, FunctionCallingConfigMode
from agents.utils import load_agent_instruction, load_agent_env, AgentName
from workflow_enums import WorkflowStage
from session_manager import get_session_manager

# Load environment variables (using a default agent or shared env)
# For orchestrator agent, we can use shared env vars or the first agent's env
load_agent_env(AgentName.CREATOR_FINDER_AGENT)

# Load instruction from external file
_full_instruction = load_agent_instruction(Path(__file__).parent)

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
    # Agent directories now use underscores (Python package naming convention)
    agent_dir = agent_name
    agent_path = _AGENTS_DIR / agent_dir / 'agent.py'
    spec = importlib.util.spec_from_file_location(agent_name, agent_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # Frontdesk agent exports as 'frontdesk', others export with their full name
    if agent_enum == AgentName.FRONTDESK_AGENT:
        return getattr(module, 'frontdesk')
    return getattr(module, agent_name)


# Load all specialized agents (NOT wrapped with AgentTool to preserve context)
# Stored in a dict to prevent judge_agent.py from picking them up as the main agent
_sub_agents = {
    AgentName.ONBOARDING_AGENT: _load_agent(AgentName.ONBOARDING_AGENT),
    AgentName.CREATOR_FINDER_AGENT: _load_agent(AgentName.CREATOR_FINDER_AGENT),
    AgentName.CAMPAIGN_BRIEF_AGENT: _load_agent(AgentName.CAMPAIGN_BRIEF_AGENT),
    AgentName.OUTREACH_MESSAGE_AGENT: _load_agent(AgentName.OUTREACH_MESSAGE_AGENT),
    AgentName.CAMPAIGN_BUILDER_AGENT: _load_agent(AgentName.CAMPAIGN_BUILDER_AGENT),
    AgentName.FRONTDESK_AGENT: _load_agent(AgentName.FRONTDESK_AGENT),
}


def _get_session_memory_from_context(tool_context: ToolContext):
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


def _build_frontdesk_fallback(tool_context: ToolContext) -> str:
    """Provide a minimal fallback payload for frontdesk when upstream returned empty."""
    session_memory = _get_session_memory_from_context(tool_context)
    if not session_memory:
        return "Please acknowledge the user's request and let them know we are continuing."

    stage = session_memory.get_workflow_stage()
    stage_text = stage.value if stage else "unspecified stage"

    messages = session_memory.get_shared_context().get("messages", [])
    last_user = next((m.get("content") for m in reversed(messages) if m.get("role") == "user"), "")
    last_user = (last_user or "").strip()

    return (
        f"User request: {last_user or 'No user text available.'} "
        f"Current workflow stage: {stage_text}. "
        "Provide a brief, friendly acknowledgement and next step for this stage."
    )


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
            print(f"[ORCHESTRATOR] Workflow stage set to {target_stage.value} for session {session_id}", flush=True)
    except Exception as e:
        print(f"[ORCHESTRATOR] Failed to set workflow stage for {agent_enum.value}: {e}", flush=True)


async def _run_agent_and_get_text(agent: Agent, tool_context: ToolContext, request: str) -> str:
    """Helper to run an agent and collect its text response using a new runner with shared session."""
    response_text = ""
    before_stage, before_card = _snapshot_session_state(tool_context)
    
    # Extract session info from tool_context
    session = getattr(tool_context, 'session', None)
    user_id = "unknown_user"
    session_id = "unknown_session"
    app_name = "agents"
    
    if session:
        user_id = getattr(session, 'user_id', user_id)
        session_id = getattr(session, 'session_id', session_id)
        app_name = getattr(session, 'app_name', app_name)
    else:
        # Generate a session_id to avoid None (silent fallback)
        session_id = f"tool_session_{agent.name}_{uuid.uuid4().hex}"
    
        print(f"[ORCHESTRATOR] Running sub-agent {agent.name} for user_id={user_id}, session_id={session_id}", flush=True)

    # Handle case where request is passed as a dict (LLM quirk)
    if isinstance(request, dict):
        if 'request' in request:
            request = request['request']
        else:
            request = str(request)
    
    print(f"[ORCHESTRATOR] Request to {agent.name}: {request}", flush=True)
    
    # Create a new runner for the sub-agent
    # The session state is managed by SessionManager, so using the same session_id
    # will give the sub-agent access to the shared session context
    try:
        # Reuse the root runner's services to preserve session state across sub-agents
        root_runner = get_session_manager().get_or_create_runner(user_id)
        runner = Runner(
            app_name=root_runner.app_name,
            agent=agent,
            artifact_service=getattr(root_runner, "artifact_service", None),
            session_service=root_runner.session_service,
            memory_service=getattr(root_runner, "memory_service", None),
            credential_service=getattr(root_runner, "credential_service", None),
        )

        # Ensure session exists in the shared session service
        existing = None
        if hasattr(root_runner.session_service, "get_session_sync"):
            existing = root_runner.session_service.get_session_sync(
                app_name=root_runner.app_name, user_id=user_id, session_id=session_id
            )
        if not existing and hasattr(root_runner.session_service, "create_session_sync"):
            root_runner.session_service.create_session_sync(
                app_name=root_runner.app_name, user_id=user_id, session_id=session_id
            )

        new_message = types.Content(role="user", parts=[types.Part(text=request)])
        
        print(f"[ORCHESTRATOR] Calling {agent.name}.run() with session_id={session_id}", flush=True)
        
        # Run the agent using the same session_id to share context
        event_stream = runner.run(
            user_id=user_id,
            session_id=session_id,
            new_message=new_message
        )
        
        event_count = 0
        text_event_count = 0
        part_count = 0
        for event in event_stream:
            event_count += 1
            print(f"[ORCHESTRATOR] Event {event_count} from {agent.name}: has_content={event.content is not None}", flush=True)
            if event.content and event.content.parts:
                parts_len = len(event.content.parts)
                part_count += parts_len
                print(f"[ORCHESTRATOR] Event {event_count} has {parts_len} parts", flush=True)
                for part in event.content.parts:
                    if hasattr(part, 'text') and part.text:
                        response_text += part.text
                        text_event_count += 1
                        print(f"[ORCHESTRATOR] Added text: {part.text[:80]}...", flush=True)

        print(
            f"[ORCHESTRATOR] Sub-agent {agent.name} completed: "
            f"events={event_count}, parts={part_count}, text_events={text_event_count}, "
            f"response_len={len(response_text)}",
            flush=True,
        )
        print(
            f"[ORCHESTRATOR] Sub-agent {agent.name} returned: "
            f"{response_text[:200] if response_text else '(empty)'}...",
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

    except Exception as e:
        error_msg = f"Error running sub-agent {agent.name}: {str(e)}"
        print(f"[ORCHESTRATOR] {error_msg}", flush=True)
        import traceback
        traceback.print_exc()
        return error_msg

    return response_text



# Custom routing tools that preserve ExecutionContext
# These replace AgentTool to avoid context isolation issues

@FunctionTool
async def route_to_onboarding_agent(
    request: str,
    tool_context: ToolContext
) -> str:
    """
    Route to onboarding agent for collecting business information.
    
    Use this when the user needs to provide or update their business details,
    or when no business card exists in the session.
    """
    _set_frontdesk_called(tool_context, False)
    _set_workflow_stage(AgentName.ONBOARDING_AGENT, tool_context)
    return await _run_agent_and_get_text(_sub_agents[AgentName.ONBOARDING_AGENT], tool_context, request)


@FunctionTool
async def route_to_creator_finder_agent(
    request: str,
    tool_context: ToolContext
) -> str:
    """
    Route to creator finder agent for searching influencers/creators.
    
    Use this when the user wants to find influencers or creators based on
    specific criteria like category, location, budget, or platform.
    """
    _set_frontdesk_called(tool_context, False)
    _set_workflow_stage(AgentName.CREATOR_FINDER_AGENT, tool_context)
    return await _run_agent_and_get_text(_sub_agents[AgentName.CREATOR_FINDER_AGENT], tool_context, request)


@FunctionTool
async def route_to_campaign_brief_agent(
    request: str,
    tool_context: ToolContext
) -> str:
    """
    Route to campaign brief agent for planning marketing campaigns.
    
    Use this when the user wants to create a campaign brief, define campaign goals,
    target audience, or marketing strategy.
    """
    _set_frontdesk_called(tool_context, False)
    _set_workflow_stage(AgentName.CAMPAIGN_BRIEF_AGENT, tool_context)
    return await _run_agent_and_get_text(_sub_agents[AgentName.CAMPAIGN_BRIEF_AGENT], tool_context, request)


@FunctionTool
async def route_to_outreach_message_agent(
    request: str,
    tool_context: ToolContext
) -> str:
    """
    Route to outreach message agent for creating influencer outreach messages.
    
    Use this when the user wants to craft personalized messages to reach out
    to influencers or creators for collaboration.
    """
    _set_frontdesk_called(tool_context, False)
    _set_workflow_stage(AgentName.OUTREACH_MESSAGE_AGENT, tool_context)
    return await _run_agent_and_get_text(_sub_agents[AgentName.OUTREACH_MESSAGE_AGENT], tool_context, request)


@FunctionTool
async def route_to_campaign_builder_agent(
    request: str,
    tool_context: ToolContext
) -> str:
    """
    Route to campaign builder agent for assembling complete campaigns.
    
    Use this when the user wants to create a full campaign package with
    creators, briefs, timelines, and deliverables.
    """
    _set_frontdesk_called(tool_context, False)
    _set_workflow_stage(AgentName.CAMPAIGN_BUILDER_AGENT, tool_context)
    return await _run_agent_and_get_text(_sub_agents[AgentName.CAMPAIGN_BUILDER_AGENT], tool_context, request)


@FunctionTool
async def route_to_frontdesk_agent(
    request: str,
    tool_context: ToolContext
) -> str:
    """
    Route to frontdesk agent for formatting responses for end users.
    
    ALWAYS call this LAST to ensure responses are user-friendly and properly formatted.
    Use this to convert technical/system outputs into conversational, helpful responses.
    """
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

    if not specialist_text.strip():
        specialist_text = "No specialist response was generated."

    payload = (
        f"Workflow stage: {stage_text}. "
        f"User request: {last_user or 'No user text available.'} "
        f"Specialist response: {specialist_text}. "
        "Provide a clear, user-facing message that acknowledges the request and states the next step."
    )

    return await _run_agent_and_get_text(
        _sub_agents[AgentName.FRONTDESK_AGENT], tool_context, payload
    )


# Create routing tools list for the orchestrator
_routing_tools = [
    route_to_onboarding_agent,
    route_to_creator_finder_agent,
    route_to_campaign_brief_agent,
    route_to_outreach_message_agent,
    route_to_campaign_builder_agent,
    route_to_frontdesk_agent,
]

# Create a root agent that orchestrates workflows across other agents
# This agent analyzes user requests and delegates to the most relevant specialized agents in the system
# Uses FunctionTool routing (not AgentTool) to preserve ExecutionContext
root_agent = Agent(
    model='gemini-2.5-flash',
    name='root_agent',
    description='Workflow Orchestrator Agent that analyzes user requests and delegates to the most relevant specialized agents in the system.',
    instruction=_full_instruction,
    tools=_routing_tools,  # FunctionTools preserve context, unlike AgentTool
)
