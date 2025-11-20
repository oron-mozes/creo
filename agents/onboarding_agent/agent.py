from pathlib import Path
from google.adk.agents.llm_agent import Agent
from google.adk.tools.google_search_tool import GoogleSearchTool
from google.genai import types
from agents.utils import load_agent_instruction, load_agent_env, AgentName
from agents.onboarding_agent.tools import save_business_card

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
        'Business onboarding agent with ONE job: collect business information and save it. '
        'Assumes business card does NOT exist (orchestrator handles routing). '
        'Extracts info from user messages (name, location, service type, website, social links). '
        'Uses Google Search to find missing details when user provides website, social handle, or business name. '
        'Asks for missing required fields. Confirms with user before calling save_business_card tool.'
    ),
    instruction=_full_instruction,
    tools=[search_tool, save_business_card],
    generate_content_config=types.GenerateContentConfig(
        # LOWER = less randomness, fewer hallucinations
        temperature=0.3,
        # Keep some diversity, but not crazy
        top_p=0.8,
        # Make sure it has enough room for confirmation blocks
        max_output_tokens=512,
    ),
)
