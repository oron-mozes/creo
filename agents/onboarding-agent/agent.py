from pathlib import Path
from google.adk.agents.llm_agent import Agent
from google.adk.tools.google_search_tool import GoogleSearchTool
from agents.utils import load_agent_instruction, load_agent_env, AgentName

# Load environment variables for this agent
load_agent_env(AgentName.ONBOARDING_AGENT)

# Load instruction and examples from external files
_full_instruction = load_agent_instruction(Path(__file__).parent)

# Create a GoogleSearchTool instance with bypass flag for use in sub-agents
# This allows the tool to work when the agent is used as a sub-agent via AgentTool
search_tool = GoogleSearchTool(bypass_multi_tools_limit=True)

# Create onboarding agent with Google Search enabled
onboarding_agent = Agent(
    model='gemini-2.0-flash-exp',  # Gemini 2.0+ required for google_search
    name=AgentName.ONBOARDING_AGENT.value,
    description='You are a greeter agent. your goal is to make sure that we have information about the user business.',
    instruction=_full_instruction,
    tools=[search_tool]
)
