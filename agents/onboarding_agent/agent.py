from pathlib import Path
from google.adk.agents.llm_agent import Agent
from google.adk.tools.google_search_tool import GoogleSearchTool
from agents.utils import load_agent_instruction, load_agent_env, AgentName
from agents.onboarding_agent.tools import save_business_card, load_business_card

# Load environment variables for this agent
load_agent_env(AgentName.ONBOARDING_AGENT)

# Load instruction and examples from external files
_full_instruction = load_agent_instruction(Path(__file__).parent)

# Create a GoogleSearchTool instance with bypass flag for use in sub-agents
# This allows the tool to work when the agent is used as a sub-agent via AgentTool
search_tool = GoogleSearchTool(bypass_multi_tools_limit=True)

# Create onboarding agent with Google Search and save tool
onboarding_agent = Agent(
    model='gemini-2.5-flash',
    name=AgentName.ONBOARDING_AGENT.value,
    description=(
        'Business onboarding agent. Collects essential business information (name, location, service type, website, social links). '
        'Extracts information from conversation history and uses Google Search to find missing details proactively. '
        'Smart extraction from context to avoid redundant questions. '
        'Uses save_business_card tool to persist business card after user confirmation. '
        'Must be invoked before campaign brief creation.'
    ),
    instruction=_full_instruction,
    tools=[search_tool, save_business_card, load_business_card]
)
