from pathlib import Path
from google.adk.agents.llm_agent import Agent
from agents.utils import load_agent_instruction, load_agent_env, AgentName
from .tools import find_creators

# Load environment variables for this agent
load_agent_env(AgentName.CREATOR_FINDER_AGENT)

# Load instruction and examples from external files
_full_instruction = load_agent_instruction(Path(__file__).parent)

creator_finder_agent = Agent(
    model='gemini-2.5-flash',
    name=AgentName.CREATOR_FINDER_AGENT.value,
    description='You are a helpful assistant for finding influencers/creators based on campaign criteria.',
    instruction=_full_instruction,
    tools=[find_creators],
)
