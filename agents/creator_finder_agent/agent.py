"""Creator Finder Agent module for finding YouTube creators based on campaign criteria."""

from pathlib import Path
import logging

from google.adk.agents.llm_agent import Agent  # type: ignore[import-untyped]
from agents.utils import load_agent_instruction, load_agent_env, AgentName
from agents.creator_finder_agent.tools import find_creators
from agents.outreach_message_agent.tools_auth import require_auth_for_outreach

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables for this agent
load_agent_env(AgentName.CREATOR_FINDER_AGENT)

# Load instruction and examples from external files
_full_instruction = load_agent_instruction(Path(__file__).parent)

# Create the agent instance
creator_finder_agent = Agent(
    model='gemini-2.5-flash',
    name=AgentName.CREATOR_FINDER_AGENT.value,
    description=(
        'You are a helpful assistant for finding YouTube creators/influencers based on campaign criteria. '
        'IMPORTANT: You search YouTube Data API v3 exclusively - only YouTube channels are returned. '
        'BUDGET FILTERING: Searches use expanded budget range (80%-120%) with subscriber-based filtering. '
        'Results are flagged when estimated price exceeds max budget or is below 90% of min budget. '
        'Always start by greeting the user and explaining the budget-to-subscriber calculation BEFORE calling any tools. '
        'When parsing budget ranges: '
        '- ALWAYS extract the EXACT numbers from user input '
        '(e.g., "100-10000$" means min_price=100, max_price=10000) '
        '- Do NOT interpret or modify budget values. '
        'Treat subscribers as followers - they are equivalent metrics. '
        'Present results with subscriber count, engagement rate (views-based), video count, estimated pricing, '
        'and budget status (clearly mark ⚠️ "Above your budget" or 💡 "Below budget threshold").'
    ),
    instruction=_full_instruction,
    tools=[find_creators, require_auth_for_outreach],
)

# ADK web expects a root_agent variable in each agent module
root_agent = creator_finder_agent

logger.info("Creator Finder Agent initialized: %s", creator_finder_agent.name)
