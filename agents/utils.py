"""Shared utilities for loading agent instructions and examples."""
from pathlib import Path
import os
from typing import Optional, Dict, Union
from enum import Enum


class AgentName(str, Enum):
    """Enumeration of all agent names in the project."""
    CREATOR_FINDER_AGENT = 'creator_finder_agent'
    CAMPAIGN_BRIEF_AGENT = 'campaign_brief_agent'
    CAMPAIGN_PLANNER_AGENT = 'campaign_planner_agent'
    OUTREACH_MESSAGE_AGENT = 'outreach_message_agent'
    SUGGESTIONS_AGENT = 'suggestions_agent'

    ONBOARDING_AGENT = 'onboarding_agent'

    FRONTDESK_AGENT = 'frontdesk_agent'

    CAMPAIGN_BUILDER_AGENT = 'campaign_builder_agent'


def load_agent_env(agent_name: Union[AgentName, str], project_root: Optional[Path] = None) -> Dict[str, str]:
    """
    Load environment variables for a specific agent from the root .env file.
    
    This function:
    1. Loads all variables from the root .env file
    2. Filters variables with the agent-specific prefix (e.g., CREATOR_FINDER_AGENT_*)
    3. Sets them in the environment without the prefix
    4. Also includes any shared variables (without agent prefix)
    
    Args:
        agent_name: Name of the agent (AgentName enum or string)
        project_root: Path to project root. If None, will try to find it automatically.
        
    Returns:
        Dictionary of environment variables for the agent (without prefix)
    """
    # Convert enum to string if needed
    if isinstance(agent_name, AgentName):
        agent_name = agent_name.value
    if project_root is None:
        # Try to find project root by looking for .env file
        current = Path(__file__).parent
        while current != current.parent:
            if (current / '.env').exists():
                project_root = current
                break
            current = current.parent

        # If no .env file found (e.g., in Docker), use environment variables directly
        if project_root is None:
            # Return empty dict - env vars are already set by Docker/Cloud Run
            return {}

    env_file = project_root / '.env'
    if not env_file.exists():
        # No .env file (e.g., in Docker), use environment variables directly
        return {}
    
    # Read .env file manually to get all variables
    env_vars = {}
    with open(env_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue
            # Parse KEY=VALUE
            if '=' in line:
                key, value = line.split('=', 1)
                env_vars[key.strip()] = value.strip()
    
    # Get agent prefix (convert snake_case to UPPER_SNAKE_CASE)
    agent_prefix = agent_name.upper() + '_'
    
    # Known agent prefixes to identify shared variables (derived from enum)
    known_agent_prefixes = [agent.value.upper() + '_' for agent in AgentName]
    
    # Filter and set agent-specific variables
    agent_vars = {}
    for key, value in env_vars.items():
        if key.startswith(agent_prefix):
            # Remove prefix and set in environment
            clean_key = key[len(agent_prefix):]
            os.environ[clean_key] = value
            agent_vars[clean_key] = value
        elif not any(key.startswith(prefix) for prefix in known_agent_prefixes):
            # Include shared variables (those without any agent prefix)
            os.environ[key] = value
            agent_vars[key] = value
    
    return agent_vars


def load_agent_instruction(agent_dir: Path) -> str:
    """
    Load instruction from an agent directory.

    Args:
        agent_dir: Path to the agent directory containing instruction.md

    Returns:
        Instruction string (includes examples if they were merged)
    """
    # Read instruction from external file (now includes merged examples)
    instruction_path = agent_dir / 'instruction.md'
    with open(instruction_path, 'r', encoding='utf-8') as f:
        instruction = f.read().strip()

    return instruction

