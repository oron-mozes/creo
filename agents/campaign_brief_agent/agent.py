from pathlib import Path
from google.adk.agents.llm_agent import Agent
from agents.utils import load_agent_instruction, load_agent_env, AgentName
from agents.campaign_brief_agent.tools import save_campaign_brief

# Load environment variables for this agent
load_agent_env(AgentName.CAMPAIGN_BRIEF_AGENT)

# Load instruction and examples from external files
_full_instruction = load_agent_instruction(Path(__file__).parent)

campaign_brief_agent = Agent(
    model='gemini-2.5-flash',
    name=AgentName.CAMPAIGN_BRIEF_AGENT.value,
    description=(
        'Campaign brief creation agent. Collects campaign-specific information (goal, platform, budget, audience) '
        'while automatically inheriting business details (name, location, niche) from the business card. '
        'Extracts information from conversation history to avoid redundant questions. '
        'Requires business card to exist before invocation. '
        'Uses save_campaign_brief tool to persist the brief after user confirmation.'
    ),
    instruction=_full_instruction,
    tools=[save_campaign_brief]
)
