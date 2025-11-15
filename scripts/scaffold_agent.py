#!/usr/bin/env python3
"""Script to scaffold a new agent with all necessary files and updates."""
import sys
import re
from pathlib import Path
from typing import Tuple

# Get project root (assuming script is in scripts/ directory)
PROJECT_ROOT = Path(__file__).parent.parent
AGENTS_DIR = PROJECT_ROOT / 'agents'
UTILS_FILE = AGENTS_DIR / 'utils.py'
INIT_FILE = AGENTS_DIR / '__init__.py'
ENV_EXAMPLE = PROJECT_ROOT / '.env.example'
ORCHESTRATOR_INSTRUCTION = AGENTS_DIR / 'orchestrator-agent' / 'instruction.md'


def to_snake_case(name: str) -> str:
    """Convert agent name to snake_case."""
    # Replace hyphens and spaces with underscores
    name = re.sub(r'[- ]+', '_', name)
    # Convert to lowercase
    name = name.lower()
    # Remove any non-alphanumeric characters except underscores
    name = re.sub(r'[^a-z0-9_]', '', name)
    return name


def to_kebab_case(name: str) -> str:
    """Convert agent name to kebab-case."""
    # Replace underscores and spaces with hyphens
    name = re.sub(r'[_ ]+', '-', name)
    # Convert to lowercase
    name = name.lower()
    # Remove any non-alphanumeric characters except hyphens
    name = re.sub(r'[^a-z0-9-]', '', name)
    return name


def to_enum_name(name: str) -> str:
    """Convert agent name to ENUM_CASE."""
    snake = to_snake_case(name)
    return snake.upper()


def to_title_case(name: str) -> str:
    """Convert agent name to Title Case."""
    # Split by common separators and capitalize each word
    words = re.split(r'[-_\s]+', name)
    return ' '.join(word.capitalize() for word in words if word)


def create_agent_directory(agent_dir: Path) -> None:
    """Create the agent directory."""
    agent_dir.mkdir(parents=True, exist_ok=True)
    print(f"✓ Created directory: {agent_dir}")


def create_init_file(agent_dir: Path) -> None:
    """Create __init__.py file."""
    init_file = agent_dir / '__init__.py'
    init_file.write_text('from . import agent\n')
    print(f"✓ Created {init_file.name}")


def create_agent_file(agent_dir: Path, agent_name_snake: str, enum_name: str, description: str) -> None:
    """Create agent.py file."""
    agent_file = agent_dir / 'agent.py'
    content = f'''from pathlib import Path
from google.adk.agents.llm_agent import Agent
from agents.utils import load_agent_instruction, load_agent_env, AgentName

# Load environment variables for this agent
load_agent_env(AgentName.{enum_name})

# Load instruction and examples from external files
_full_instruction = load_agent_instruction(Path(__file__).parent)

{agent_name_snake} = Agent(
    model='gemini-2.5-flash',
    name=AgentName.{enum_name}.value,
    description='{description}',
    instruction=_full_instruction,
)
'''
    agent_file.write_text(content)
    print(f"✓ Created {agent_file.name}")


def create_instruction_file(agent_dir: Path, agent_title: str, description: str) -> None:
    """Create instruction.md file."""
    instruction_file = agent_dir / 'instruction.md'
    content = f'''{description}

You will be given information about:
- [Specify what inputs the agent expects]

You need to:
- [Specify what the agent should do]
- [Specify expected outputs]

[Add any additional instructions or guidelines]
'''
    instruction_file.write_text(content)
    print(f"✓ Created {instruction_file.name}")


def create_examples_file(agent_dir: Path) -> None:
    """Create examples.md file."""
    examples_file = agent_dir / 'examples.md'
    content = '''# Examples

## Example 1

**Input:**
- Parameter 1: value
- Parameter 2: value

**Output:**
Expected output here...

## Example 2

**Input:**
- Parameter 1: value
- Parameter 2: value

**Output:**
Expected output here...
'''
    examples_file.write_text(content)
    print(f"✓ Created {examples_file.name}")


def update_utils_file(enum_name: str) -> None:
    """Add agent to AgentName enum in utils.py."""
    content = UTILS_FILE.read_text()
    
    # Find the enum class
    enum_pattern = r'(class AgentName\(str, Enum\):.*?)(\n\n)'
    match = re.search(enum_pattern, content, re.DOTALL)
    
    if match:
        enum_content = match.group(1)
        # Check if already exists
        if enum_name in enum_content:
            print(f"⚠ {enum_name} already exists in {UTILS_FILE.name}")
            return
        
        # Add new enum value before the closing
        new_enum_line = f"    {enum_name} = '{enum_name.lower()}'\n"
        # Insert before the last line of enum
        lines = enum_content.split('\n')
        lines.insert(-1, new_enum_line)
        updated_enum = '\n'.join(lines)
        
        content = content.replace(enum_content, updated_enum)
        UTILS_FILE.write_text(content)
        print(f"✓ Updated {UTILS_FILE.name}")
    else:
        print(f"⚠ Could not find AgentName enum in {UTILS_FILE.name}")


def update_init_file(agent_name_snake: str, agent_dir_kebab: str) -> None:
    """Add agent import to __init__.py."""
    content = INIT_FILE.read_text()
    
    # Check if already imported
    if f'{agent_name_snake} = ' in content:
        print(f"⚠ {agent_name_snake} already imported in {INIT_FILE.name}")
        return
    
    # Find the last agent import section (look for any agent import pattern)
    pattern = r'(# Load .*-agent\n.*?(\w+) = _\2_module\.\2\n)'
    matches = list(re.finditer(pattern, content, re.DOTALL))
    
    if matches:
        # Get the last match
        last_match = matches[-1]
        # Add new agent import after the last one
        new_import = f'''# Load {agent_dir_kebab}
_{agent_name_snake}_path = _agents_dir / '{agent_dir_kebab}' / 'agent.py'
_{agent_name_snake}_spec = importlib.util.spec_from_file_location('{agent_name_snake}', _{agent_name_snake}_path)
_{agent_name_snake}_module = importlib.util.module_from_spec(_{agent_name_snake}_spec)
_{agent_name_snake}_spec.loader.exec_module(_{agent_name_snake}_module)
{agent_name_snake} = _{agent_name_snake}_module.{agent_name_snake}

'''
        content = content.replace(last_match.group(1), last_match.group(1) + new_import)
        
        # Update __all__ list - find the last entry
        if '__all__ = [' in content:
            all_pattern = r"(__all__ = \[.*?'(\w+)',\n)"
            all_matches = list(re.finditer(all_pattern, content, re.DOTALL))
            if all_matches:
                last_all_match = all_matches[-1]
                content = content.replace(
                    last_all_match.group(1),
                    last_all_match.group(1) + f"    '{agent_name_snake}',\n"
                )
        
        INIT_FILE.write_text(content)
        print(f"✓ Updated {INIT_FILE.name}")
    else:
        print(f"⚠ Could not find insertion point in {INIT_FILE.name}")


def update_env_example(enum_name: str, agent_title: str) -> None:
    """Add agent to .env.example."""
    if not ENV_EXAMPLE.exists():
        print(f"⚠ {ENV_EXAMPLE.name} does not exist, skipping")
        return
    
    content = ENV_EXAMPLE.read_text()
    
    # Check if already exists
    if enum_name in content:
        print(f"⚠ {enum_name} already exists in {ENV_EXAMPLE.name}")
        return
    
    # Add at the end
    new_env = f'''

# {agent_title} specific variables
# Variables prefixed with {enum_name}_ will be available without the prefix for this agent
{enum_name}_GOOGLE_API_KEY=your-api-key-here
'''
    content += new_env
    ENV_EXAMPLE.write_text(content)
    print(f"✓ Updated {ENV_EXAMPLE.name}")


def update_orchestrator_instruction(agent_name_snake: str, agent_title: str) -> None:
    """Add agent to orchestrator instruction."""
    if not ORCHESTRATOR_INSTRUCTION.exists():
        print(f"⚠ {ORCHESTRATOR_INSTRUCTION.name} does not exist, skipping")
        return
    
    content = ORCHESTRATOR_INSTRUCTION.read_text()
    
    # Check if already exists
    if agent_name_snake in content:
        print(f"⚠ {agent_name_snake} already exists in orchestrator instruction")
        return
    
    # Find the last agent in the list (look for numbered list items)
    pattern = r'(\d+)\. (\w+) - (.+\n)'
    matches = list(re.finditer(pattern, content))
    
    if matches:
        # Get the last match
        last_match = matches[-1]
        last_number = int(last_match.group(1))
        new_number = last_number + 1
        # Add new agent
        new_agent = f"{new_number}. {agent_name_snake} - {agent_title}\n"
        content = content.replace(last_match.group(0), last_match.group(0) + new_agent)
        ORCHESTRATOR_INSTRUCTION.write_text(content)
        print(f"✓ Updated {ORCHESTRATOR_INSTRUCTION.name}")
    else:
        print(f"⚠ Could not find insertion point in {ORCHESTRATOR_INSTRUCTION.name}")


def main():
    """Main function to scaffold a new agent."""
    if len(sys.argv) < 2:
        print("Usage: python scripts/scaffold_agent.py <agent-name> [description]")
        print("\nExample:")
        print("  python scripts/scaffold_agent.py 'Content Creator' 'Helps create content for campaigns'")
        sys.exit(1)
    
    agent_name = sys.argv[1]
    description = sys.argv[2] if len(sys.argv) > 2 else f"Agent for {agent_name}"
    
    # Convert to various formats
    agent_name_snake = to_snake_case(agent_name)
    agent_name_kebab = to_kebab_case(agent_name)
    enum_name = to_enum_name(agent_name)
    agent_title = to_title_case(agent_name)
    
    print(f"\n🚀 Scaffolding new agent: {agent_title}")
    print(f"   Directory: agents/{agent_name_kebab}")
    print(f"   Enum name: {enum_name}")
    print()
    
    # Create directory structure
    agent_dir = AGENTS_DIR / agent_name_kebab
    create_agent_directory(agent_dir)
    create_init_file(agent_dir)
    create_agent_file(agent_dir, agent_name_snake, enum_name, description)
    create_instruction_file(agent_dir, agent_title, description)
    create_examples_file(agent_dir)
    
    # Update existing files
    print("\n📝 Updating existing files...")
    update_utils_file(enum_name)
    update_init_file(agent_name_snake, agent_name_kebab)
    update_env_example(enum_name, agent_title)
    update_orchestrator_instruction(agent_name_snake, agent_title)
    
    print(f"\n✅ Successfully scaffolded {agent_title}!")
    print(f"\n📋 Next steps:")
    print(f"   1. Edit agents/{agent_name_kebab}/instruction.md with detailed instructions")
    print(f"   2. Edit agents/{agent_name_kebab}/examples.md with real examples")
    print(f"   3. Add your API key to .env file: {enum_name}_GOOGLE_API_KEY=your-key")
    print(f"   4. Test your agent: make web")


if __name__ == '__main__':
    main()

