"""Workflow Orchestrator agent for ADK web interface."""
from pathlib import Path
import importlib.util
from google.adk.agents.llm_agent import Agent
from google.adk.tools.agent_tool import AgentTool
from agents.utils import load_agent_instruction, load_agent_env, AgentName

# Load environment variables (using a default agent or shared env)
# For orchestrator agent, we can use shared env vars or the first agent's env
load_agent_env(AgentName.CREATOR_FINDER_AGENT)

# Load instruction from external file
_full_instruction = load_agent_instruction(Path(__file__).parent)

_AGENTS_DIR = Path(__file__).resolve().parent.parent
_AGENT_ENUMS = [
    AgentName.ONBOARDING_AGENT,  # Collect business information first
    AgentName.CREATOR_FINDER_AGENT,
    AgentName.CAMPAIGN_BRIEF_AGENT,
    AgentName.OUTREACH_MESSAGE_AGENT,
    AgentName.CAMPAIGN_BUILDER_AGENT,
    AgentName.FRONTDESK_AGENT,  # ALWAYS called last to format responses for users
]


def _load_agent(agent_enum: AgentName) -> Agent:
    """Import an agent module dynamically and return the Agent instance."""
    agent_name = agent_enum.value
    agent_dir = agent_name.replace('_', '-')
    agent_path = _AGENTS_DIR / agent_dir / 'agent.py'
    spec = importlib.util.spec_from_file_location(agent_name, agent_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # Frontdesk agent exports as 'frontdesk', others export with their full name
    if agent_enum == AgentName.FRONTDESK_AGENT:
        return getattr(module, 'frontdesk')
    return getattr(module, agent_name)


# Load all agents that will be used as tools
_agents = [_load_agent(enum) for enum in _AGENT_ENUMS]

# Wrap each agent as an AgentTool so they can be used as tools
# This allows agents with different tool types (GoogleSearchTool, custom functions, etc.)
# to work together without triggering "Multiple tools are supported only when they are all search tools" error
_agent_tools = [AgentTool(agent=agent) for agent in _agents]

# Create a root agent that orchestrates workflows across other agents
# This agent analyzes user requests and delegates to the appropriate specialized agents
# Agents are used as tools (via AgentTool), not as sub_agents parameter
root_agent = Agent(
    model='gemini-2.5-flash',
    name='root_agent',
    description='Workflow Orchestrator Agent that analyzes user requests and delegates to the most relevant specialized agents in the system.',
    instruction=_full_instruction,
    tools=_agent_tools,
)
