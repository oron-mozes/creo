from pathlib import Path
from google.adk.agents.llm_agent import Agent
from agents.utils import load_agent_instruction, load_agent_env, AgentName
from agents.creator_finder_agent.tools import search_influencers

# Load environment variables for this agent
load_agent_env(AgentName.CREATOR_FINDER_AGENT)

# Load instruction and examples from external files
_full_instruction = load_agent_instruction(Path(__file__).parent)

creator_finder_agent = Agent(
    model='gemini-2.5-flash',
    name=AgentName.CREATOR_FINDER_AGENT.value,
    description='Finds and recommends influencers/creators for marketing campaigns using semantic search. Interprets user requirements (niche, location, audience demographics, budget, performance history) and searches a vector database of influencers to provide ranked, data-driven recommendations.',
    instruction=_full_instruction,
    tools=[search_influencers]
)
