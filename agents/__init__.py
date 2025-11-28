"""Agents package for the creo project - Single Agent Mode: creator-finder."""
import importlib.util
import os
from pathlib import Path

_agents_dir = Path(__file__).parent

if os.environ.get("CREO_SKIP_AGENT_AUTOLOAD") != "1":
    # Load creator_finder_agent
    _agent_path = _agents_dir / 'creator_finder_agent' / 'agent.py'
    _agent_spec = importlib.util.spec_from_file_location('creator_finder_agent', _agent_path)
    if _agent_spec is None or _agent_spec.loader is None:
        raise RuntimeError("Unable to load creator_finder_agent module spec")
    _agent_module = importlib.util.module_from_spec(_agent_spec)
    _agent_spec.loader.exec_module(_agent_module)
    creator_finder_agent = _agent_module.creator_finder_agent
    root_agent = _agent_module.root_agent  # Each agent should have root_agent
else:
    creator_finder_agent = None
    root_agent = None

__all__ = ['root_agent', 'creator_finder_agent']
