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
from typing import Any
from google.adk.agents.llm_agent import Agent
from google.adk.tools.function_tool import FunctionTool
from google.adk.tools.tool_context import ToolContext
from agents.utils import load_agent_instruction, load_agent_env, AgentName

# Load environment variables (using a default agent or shared env)
# For orchestrator agent, we can use shared env vars or the first agent's env
load_agent_env(AgentName.CREATOR_FINDER_AGENT)

# Load instruction from external file
_full_instruction = load_agent_instruction(Path(__file__).parent)

_AGENTS_DIR = Path(__file__).resolve().parent.parent


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
_onboarding_agent = _load_agent(AgentName.ONBOARDING_AGENT)
_creator_finder_agent = _load_agent(AgentName.CREATOR_FINDER_AGENT)
_campaign_brief_agent = _load_agent(AgentName.CAMPAIGN_BRIEF_AGENT)
_outreach_message_agent = _load_agent(AgentName.OUTREACH_MESSAGE_AGENT)
_campaign_builder_agent = _load_agent(AgentName.CAMPAIGN_BUILDER_AGENT)
_frontdesk_agent = _load_agent(AgentName.FRONTDESK_AGENT)


# Custom routing tools that preserve ExecutionContext
# These replace AgentTool to avoid context isolation issues

@FunctionTool
async def route_to_onboarding_agent(
    request: str,
    tool_context: ToolContext
) -> str:
    """
    Route to onboarding agent for collecting business card information.

    Use this when the user needs to provide or update their business details
    (name, location, service type, website, social links).

    CONTEXT PRESERVATION: This tool invokes the agent directly (not via AgentTool)
    to preserve conversation history and workflow state, enabling reliable tool calling.
    """
    # Direct invocation preserves ExecutionContext (like NestJS REQUEST scope)
    result = await _onboarding_agent.run_async(request, tool_context)
    return result.text


@FunctionTool
async def route_to_creator_finder_agent(
    request: str,
    tool_context: ToolContext
) -> str:
    """
    Route to creator finder agent for searching influencers/creators.

    Use this when the user wants to find creators matching specific criteria
    (platform, follower count, niche, location, etc.).
    """
    result = await _creator_finder_agent.run_async(request, tool_context)
    return result.text


@FunctionTool
async def route_to_campaign_brief_agent(
    request: str,
    tool_context: ToolContext
) -> str:
    """
    Route to campaign brief agent for creating marketing campaign specifications.

    Use this when the user wants to define campaign goals, messaging, timeline,
    budget, or other campaign parameters.
    """
    result = await _campaign_brief_agent.run_async(request, tool_context)
    return result.text


@FunctionTool
async def route_to_outreach_message_agent(
    request: str,
    tool_context: ToolContext
) -> str:
    """
    Route to outreach message agent for drafting creator collaboration messages.

    Use this when the user wants to create personalized outreach messages
    for contacting influencers or creators.
    """
    result = await _outreach_message_agent.run_async(request, tool_context)
    return result.text


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
    result = await _campaign_builder_agent.run_async(request, tool_context)
    return result.text


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
    result = await _frontdesk_agent.run_async(request, tool_context)
    return result.text


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
# This agent analyzes user requests and delegates to the appropriate specialized agents
# Uses FunctionTool routing (not AgentTool) to preserve ExecutionContext
root_agent = Agent(
    model='gemini-2.5-flash',
    name='root_agent',
    description='Workflow Orchestrator Agent that analyzes user requests and delegates to the most relevant specialized agents in the system.',
    instruction=_full_instruction,
    tools=_routing_tools,  # FunctionTools preserve context, unlike AgentTool
)
