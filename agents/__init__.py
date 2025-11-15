"""Agents package for the creo project."""

# Import root_agent first (ADK requires this)
# Load orchestrator-agent using importlib to handle hyphens in directory name
import importlib.util
from pathlib import Path

_agents_dir = Path(__file__).parent

# Load orchestrator-agent (contains root_agent)
_orchestrator_path = _agents_dir / 'orchestrator-agent' / 'agent.py'
_orchestrator_spec = importlib.util.spec_from_file_location('orchestrator_agent', _orchestrator_path)
_orchestrator_module = importlib.util.module_from_spec(_orchestrator_spec)
_orchestrator_spec.loader.exec_module(_orchestrator_module)
root_agent = _orchestrator_module.root_agent

# Import all agents so ADK can discover them
# Note: Directory names use hyphens, so we use importlib.util to load from file paths

# Load creator-finder-agent
_creator_finder_path = _agents_dir / 'creator-finder-agent' / 'agent.py'
_creator_finder_spec = importlib.util.spec_from_file_location('creator_finder_agent', _creator_finder_path)
_creator_finder_module = importlib.util.module_from_spec(_creator_finder_spec)
_creator_finder_spec.loader.exec_module(_creator_finder_module)
creator_finder_agent = _creator_finder_module.creator_finder_agent

# Load campaing-brief-agent
_campaing_brief_path = _agents_dir / 'campaing-brief-agent' / 'agent.py'
_campaing_brief_spec = importlib.util.spec_from_file_location('campaing_brief_agent', _campaing_brief_path)
_campaing_brief_module = importlib.util.module_from_spec(_campaing_brief_spec)
_campaing_brief_spec.loader.exec_module(_campaing_brief_module)
campaing_brief_agent = _campaing_brief_module.campaing_brief_agent

# Load outreach-message-agent
_outreach_message_path = _agents_dir / 'outreach-message-agent' / 'agent.py'
_outreach_message_spec = importlib.util.spec_from_file_location('outreach_message_agent', _outreach_message_path)
_outreach_message_module = importlib.util.module_from_spec(_outreach_message_spec)
_outreach_message_spec.loader.exec_module(_outreach_message_module)
outreach_message_agent = _outreach_message_module.outreach_message_agent

# Load campaign-builder-agent
_campaign_builder_path = _agents_dir / 'campaign-builder-agent' / 'agent.py'
_campaign_builder_spec = importlib.util.spec_from_file_location('campaign_builder_agent', _campaign_builder_path)
_campaign_builder_module = importlib.util.module_from_spec(_campaign_builder_spec)
_campaign_builder_spec.loader.exec_module(_campaign_builder_module)
campaign_builder_agent = _campaign_builder_module.campaign_builder_agent

__all__ = [
    'root_agent',
    'creator_finder_agent',
    'campaing_brief_agent',
    'outreach_message_agent',
    'campaign_builder_agent',
]
