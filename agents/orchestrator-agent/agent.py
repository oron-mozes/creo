"""Workflow Orchestrator agent for ADK web interface."""
from pathlib import Path
import importlib.util
from google.adk.agents.llm_agent import Agent
from agents.utils import load_agent_instruction, load_agent_env, AgentName

# Load environment variables (using a default agent or shared env)
# For orchestrator agent, we can use shared env vars or the first agent's env
load_agent_env(AgentName.CREATOR_FINDER_AGENT)

# Load instruction from external file
_full_instruction = load_agent_instruction(Path(__file__).parent)

_AGENTS_DIR = Path(__file__).resolve().parent.parent
_SUB_AGENT_ENUMS = [
    AgentName.CREATOR_FINDER_AGENT,
    AgentName.CAMPAING_BRIEF_AGENT,
    AgentName.OUTREACH_MESSAGE_AGENT,
    AgentName.CAMPAIGN_BUILDER_AGENT,
]


def _load_sub_agent(agent_enum: AgentName) -> Agent:
    """Import a sub-agent module dynamically and return the Agent instance."""
    agent_name = agent_enum.value
    agent_dir = agent_name.replace('_', '-')
    agent_path = _AGENTS_DIR / agent_dir / 'agent.py'
    spec = importlib.util.spec_from_file_location(agent_name, agent_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, agent_name)


_sub_agents = [_load_sub_agent(enum) for enum in _SUB_AGENT_ENUMS]

# Create a root agent that orchestrates workflows across other agents
# This agent analyzes user requests and redirects them to the appropriate specialized agents
# The agents parameter links the sub-agents to the orchestrator using their enum values
root_agent = Agent(
    model='gemini-2.5-flash',
    name='root_agent',
    description='Workflow Orchestrator Agent that analyzes user requests and redirects them to the most relevant specialized agents in the system.',
    instruction=_full_instruction,
    sub_agents=_sub_agents,
)
