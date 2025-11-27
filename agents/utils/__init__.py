"""Shared utilities for loading agent instructions and environment."""
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

    1) Loads all variables from .env
    2) Filters by agent-specific prefix (e.g., CREATOR_FINDER_AGENT_*)
    3) Sets them in the environment without the prefix
    4) Includes shared variables (without agent prefix)
    """
    # Convert enum to string if needed
    if isinstance(agent_name, AgentName):
        agent_name = agent_name.value
    if project_root is None:
        current = Path(__file__).parent
        while current != current.parent:
            if (current / '.env').exists():
                project_root = current
                break
            current = current.parent
        if project_root is None:
            return {}

    env_file = project_root / '.env'
    if not env_file.exists():
        return {}

    env_vars = {}
    with open(env_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' in line:
                key, value = line.split('=', 1)
                env_vars[key.strip()] = value.strip()

    agent_prefix = agent_name.upper() + '_'
    known_agent_prefixes = [agent.value.upper() + '_' for agent in AgentName]

    agent_vars = {}
    for key, value in env_vars.items():
        if key.startswith(agent_prefix):
            clean_key = key[len(agent_prefix):]
            os.environ[clean_key] = value
            agent_vars[clean_key] = value
        elif not any(key.startswith(prefix) for prefix in known_agent_prefixes):
            os.environ[key] = value
            agent_vars[key] = value

    return agent_vars


def load_agent_instruction(agent_dir: Path) -> str:
    """Load instruction.md from an agent directory."""
    instruction_path = agent_dir / 'instruction.md'
    with open(instruction_path, 'r', encoding='utf-8') as f:
        instruction = f.read().strip()
    return instruction


__all__ = ["AgentName", "load_agent_env", "load_agent_instruction"]
