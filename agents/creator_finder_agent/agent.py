"""Creator Finder Agent module for finding influencers/creators based on campaign criteria."""

from pathlib import Path
import logging

from google.adk.agents.llm_agent import Agent  # type: ignore[import-untyped]
from agents.utils import load_agent_instruction, load_agent_env, AgentName
from agents.creator_finder_agent.tools import find_creators

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
        'You are a helpful assistant for finding influencers/creators based on campaign criteria. '
        'You ALWAYS use the find_creators tool to find creators according to the users request. '
        'Use whatever information the user gave you to find relevant creators. '
        'When parsing budget ranges: '
        '- ALWAYS extract the EXACT numbers from user input '
        '(e.g., "100-10000$" means min_price=100, max_price=10000) '
        '- Do NOT interpret or modify budget values '
        '(e.g., do NOT change "100-10000" to "10000-15000") '
        'When the user mentions target audience: '
        '- Age ranges (e.g., "18-24", "25-34") and age keywords '
        '(e.g., "millennials"=28-43, "gen z"=18-27, "teens"=13-19) '
        'are converted to numeric ranges and matched against audience_age_range. '
        'A creator matches if ANY part of their age range falls within the target range. '
        '- Topics/interests (e.g., "fitness", "gaming", "food") are matched against '
        'the audience_interests field. '
        'When referencing a gender, see which field is higher: '
        'audience_gender_male or audience_gender_female. '
        'When referencing a geographical area, look at the location_country and location_city fields. '
        'When referencing a category or niche, look at the subcategory, '
        'audience_interests, and content_themes fields.'
    ),
    instruction=_full_instruction,
    tools=[find_creators],
)

# ADK web expects a root_agent variable in each agent module
root_agent = creator_finder_agent

logger.info("Creator Finder Agent initialized: %s", creator_finder_agent.name)
