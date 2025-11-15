"""Workflow Orchestrator agent for ADK web interface."""
from pathlib import Path
from google.adk.agents.llm_agent import Agent
from agents.utils import load_agent_instruction, load_agent_env, AgentName

# Load environment variables (using a default agent or shared env)
# For orchestrator agent, we can use shared env vars or the first agent's env
load_agent_env(AgentName.CREATOR_FINDER_AGENT)

# Load instruction from external file
_full_instruction = load_agent_instruction(Path(__file__).parent)

# Create a root agent that orchestrates workflows across other agents
# This agent helps users understand what agents are available and routes them appropriately
root_agent = Agent(
    model='gemini-2.5-flash',
    name='root_agent',
    description='Workflow Orchestrator Agent that provides access to all available agents in the system and helps coordinate workflows.',
    instruction=_full_instruction,
)

