from pathlib import Path
import logging
import sys

print("DEBUG: Starting agent.py import", file=sys.stderr, flush=True)

from google.adk.agents.llm_agent import Agent
print("DEBUG: Imported Agent", file=sys.stderr, flush=True)

from agents.utils import load_agent_instruction, load_agent_env, AgentName
print("DEBUG: Imported utils", file=sys.stderr, flush=True)

# Set up debug logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

logger.info("="*80)
logger.info("CREATOR FINDER AGENT MODULE LOADING")
logger.info("="*80)
print("DEBUG: About to load environment variables", file=sys.stderr, flush=True)

# Load environment variables for this agent
logger.info("Loading environment variables...")
load_agent_env(AgentName.CREATOR_FINDER_AGENT)
logger.info("Environment variables loaded")
print("DEBUG: Environment variables loaded", file=sys.stderr, flush=True)

# Load instruction and examples from external files
logger.info("Loading instructions...")
_full_instruction = load_agent_instruction(Path(__file__).parent)
logger.info(f"Instructions loaded: {len(_full_instruction)} characters")
print(f"DEBUG: Instructions loaded: {len(_full_instruction)} characters", file=sys.stderr, flush=True)

# Lazy import tools to avoid hanging during module load
logger.info("Importing tools...")
print("DEBUG: About to import tools", file=sys.stderr, flush=True)
from agents.creator_finder_agent.tools import find_creators
logger.info("Tools imported successfully")
print("DEBUG: Tools imported successfully", file=sys.stderr, flush=True)

logger.info("Creating agent instance...")
print("DEBUG: About to create Agent instance", file=sys.stderr, flush=True)
creator_finder_agent = Agent(
    model='gemini-2.5-flash',
    name=AgentName.CREATOR_FINDER_AGENT.value,
    description='''You are a helpful assistant for finding influencers/creators based on campaign criteria.
    You ALWAYS use the find_creators tool to find creators according to the users request.
    Use whatever infortmaion the user gave you to find relevant creators.
    When referencing audience, look at the audience_age_range field in the DB.
    When referencing ages, look at audience_age_range.
    When referencing a gender, see which field is higher: audience_gender_male or audience_gender_female.
    When referencing a geographical area, look at the location_country, and location_city fields.
    When referencing a category or niche, look at the subcategory, audience_interests, and content_themes fields.''',
    instruction=_full_instruction,
    tools=[find_creators],
)
print("DEBUG: Agent instance created", file=sys.stderr, flush=True)

# ADK web expects a root_agent variable in each agent module
root_agent = creator_finder_agent
print("DEBUG: root_agent assigned", file=sys.stderr, flush=True)

logger.info(f"Agent created: {creator_finder_agent.name}")
logger.info("="*80)
print("DEBUG: agent.py module load complete", file=sys.stderr, flush=True)
