from pathlib import Path
from google.adk.agents.llm_agent import Agent
from agents.utils import load_agent_instruction, load_agent_env, AgentName

# Load environment variables for this agent
load_agent_env(AgentName.CAMPAIGN_BUILDER_AGENT)

# Load instruction and examples from external files
_full_instruction = load_agent_instruction(Path(__file__).parent)

campaign_builder_agent = Agent(
    model='gemini-2.5-flash',
    name=AgentName.CAMPAIGN_BUILDER_AGENT.value,
    description='You are a helpful assistant for building comprehensive marketing campaigns.',
    instruction=_full_instruction,
)

