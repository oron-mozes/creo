from pathlib import Path
from google.adk.agents.llm_agent import Agent
from agents.utils import load_agent_instruction, load_agent_env, AgentName

# Load environment variables for this agent
load_agent_env(AgentName.SUGGESTIONS_AGENT)

# Load instruction and examples from external files
_full_instruction = load_agent_instruction(Path(__file__).parent)

suggestions_agent = Agent(
    model='gemini-2.5-flash',
    name=AgentName.SUGGESTIONS_AGENT.value,
    description='You are a creative agent that suggest campigns idea',
    instruction=_full_instruction,
)
