from pathlib import Path
from google.adk.agents.llm_agent import Agent
from agents.utils import load_agent_instruction, load_agent_env, AgentName

# Load environment variables for this agent
load_agent_env(AgentName.FRONTDESK_AGENT)

# Load instruction and examples from external files
_full_instruction = load_agent_instruction(Path(__file__).parent)

frontdesk = Agent(
    model='gemini-2.5-flash',
    name=AgentName.FRONTDESK_AGENT.value,
    description='Transform technical information into warm, professional messages. You are the friendly voice of Creo - conversational, helpful, and always at eye-level with users.',
    instruction=_full_instruction,
)
