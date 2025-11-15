from pathlib import Path
from google.adk.agents.llm_agent import Agent
from agents.utils import load_agent_instruction, load_agent_env, AgentName

# Load environment variables for this agent
load_agent_env(AgentName.OUTREACH_MESSAGE_AGENT)

# Load instruction and examples from external files
_full_instruction = load_agent_instruction(Path(__file__).parent)

outreach_message_agent = Agent(
    model='gemini-2.5-flash',
    name=AgentName.OUTREACH_MESSAGE_AGENT.value,
    description='You are a helpful assistant for creating outreach messages to creators and influencers.',
    instruction=_full_instruction,
)

