"""Workflow Orchestrator agent for ADK web interface."""
from pathlib import Path

from google.adk.agents.llm_agent import Agent

from agents.utils import AgentName, load_agent_env, load_agent_instruction
from agents.orchestrator_agent.tools import routing_tools

# Load environment variables (using a default agent or shared env)
load_agent_env(AgentName.CREATOR_FINDER_AGENT)

# Load instruction from external file
_full_instruction = load_agent_instruction(Path(__file__).parent)

# Root orchestrator agent with routing tools
root_agent = Agent(
    model="gemini-2.5-flash",
    name="root_agent",
    description="Workflow Orchestrator Agent that analyzes user requests and delegates to the most relevant specialized agents in the system.",
    instruction=_full_instruction,
    tools=list(routing_tools),  # FunctionTools preserve context across sub-agent calls
)
