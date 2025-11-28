#!/usr/bin/env python3
"""Script to run ADK web interface with a specific agent exposed.

This script temporarily modifies agents/__init__.py to only expose the selected agent,
then runs adk web, and restores the original file when done.
"""
import sys
import os
import subprocess
import shutil
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).parent.parent
AGENTS_INIT = PROJECT_ROOT / "agents" / "__init__.py"
AGENTS_INIT_BACKUP = PROJECT_ROOT / "agents" / "__init__.py.backup"

# Map of agent names to (module_name, agent_variable_name, directory_name)
AGENT_MODULES = {
    "creator-finder": ("creator_finder_agent", "creator_finder_agent", "creator_finder_agent"),
    "campaign-builder": ("campaign_builder_agent", "campaign_builder_agent", "campaign_builder_agent"),
    "campaign-brief": ("campaign_brief_agent", "campaign_brief_agent", "campaign_brief_agent"),
    "outreach-message": ("outreach_message_agent", "outreach_message_agent", "outreach_message_agent"),
    "orchestrator": ("orchestrator_agent", "root_agent", "orchestrator_agent"),
}

def get_original_init_content() -> str:
    """Read the original __init__.py content."""
    return AGENTS_INIT.read_text()

def create_single_agent_init(agent_name: str) -> str:
    """Create __init__.py content that only exposes the specified agent."""
    if agent_name not in AGENT_MODULES:
        raise ValueError(f"Unknown agent: {agent_name}. Available: {list(AGENT_MODULES.keys())}")
    
    module_name, agent_var, agent_dir = AGENT_MODULES[agent_name]
    
    if agent_name == "orchestrator":
        # For orchestrator, we only need root_agent
        return f'''"""Agents package for the creo project - Single Agent Mode: {agent_name}."""
import importlib.util
from pathlib import Path

_agents_dir = Path(__file__).parent

# Load {agent_dir}
_agent_path = _agents_dir / '{agent_dir}' / 'agent.py'
_agent_spec = importlib.util.spec_from_file_location('{module_name}', _agent_path)
_agent_module = importlib.util.module_from_spec(_agent_spec)
_agent_spec.loader.exec_module(_agent_module)
root_agent = _agent_module.{agent_var}

__all__ = ['root_agent']
'''
    else:
        # For other agents, DON'T load orchestrator to avoid circular dependencies
        # The agent should expose its own root_agent
        return f'''"""Agents package for the creo project - Single Agent Mode: {agent_name}."""
import importlib.util
from pathlib import Path

_agents_dir = Path(__file__).parent

# Load {agent_dir}
_agent_path = _agents_dir / '{agent_dir}' / 'agent.py'
_agent_spec = importlib.util.spec_from_file_location('{module_name}', _agent_path)
_agent_module = importlib.util.module_from_spec(_agent_spec)
_agent_spec.loader.exec_module(_agent_module)
{agent_var} = _agent_module.{agent_var}
root_agent = _agent_module.root_agent  # Each agent should have root_agent

__all__ = ['root_agent', '{agent_var}']
'''

def restore_original_init() -> None:
    """Restore the original __init__.py file."""
    if AGENTS_INIT_BACKUP.exists():
        shutil.copy(AGENTS_INIT_BACKUP, AGENTS_INIT)
        AGENTS_INIT_BACKUP.unlink()
        print("✓ Restored original agents/__init__.py")

def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python scripts/web_agent.py <agent-name>")
        print("\nAvailable agents:")
        for name in AGENT_MODULES.keys():
            print(f"  - {name}")
        sys.exit(1)
    
    agent_name = sys.argv[1]
    
    if agent_name not in AGENT_MODULES:
        print(f"Error: Unknown agent '{agent_name}'")
        print(f"Available agents: {', '.join(AGENT_MODULES.keys())}")
        sys.exit(1)
    
    # Backup original file
    if not AGENTS_INIT_BACKUP.exists():
        shutil.copy(AGENTS_INIT, AGENTS_INIT_BACKUP)
        print(f"✓ Backed up original agents/__init__.py")
    
    try:
        # Create single-agent version
        new_content = create_single_agent_init(agent_name)
        AGENTS_INIT.write_text(new_content)
        print(f"✓ Modified agents/__init__.py to expose only: {agent_name}")
        print(f"  Starting ADK web interface...")
        print(f"  Press Ctrl+C to stop and restore original file\n")
        
        # Run adk web
        # Try to use venv if it exists, otherwise use system Python
        if sys.platform == "win32":
            venv_adk = PROJECT_ROOT / "venv" / "Scripts" / "adk.exe"
        else:
            venv_adk = PROJECT_ROOT / "venv" / "bin" / "adk"

        if venv_adk.exists():
            result = subprocess.run([str(venv_adk), "web", "agents", "--port", "3000"], cwd=PROJECT_ROOT, capture_output=False)
            if result.returncode != 0:
                print(f"Error: ADK web exited with code {result.returncode}")
        else:
            # Fall back to running adk from current Python environment
            print(f"Running: {sys.executable} -m google.adk.cli web agents --port 3000")
            print(f"Access the web UI at: http://localhost:3000")
            result = subprocess.run([sys.executable, "-m", "google.adk.cli", "web", "agents", "--port", "3000"], cwd=PROJECT_ROOT, capture_output=False)
            if result.returncode != 0:
                print(f"Error: ADK web exited with code {result.returncode}")
        
    except KeyboardInterrupt:
        print("\n\nStopping...")
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)
    finally:
        # Always restore original file
        restore_original_init()

if __name__ == "__main__":
    main()
