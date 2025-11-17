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
    description=(
        'User-facing message formatter agent. Transforms technical responses from other agents into warm, conversational messages. '
        'Always invoked LAST in the workflow to format final responses for users. '
        'Removes technical jargon, confirmation blocks, and internal data structures. '
        'Maintains friendly, professional tone while preserving key information. '
        'Acts as the voice of Creo - conversational, helpful, and at eye-level with users.'
    ),
    instruction=_full_instruction,
)
