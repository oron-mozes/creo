#!/usr/bin/env python3
"""Merge instruction.md and examples.md files for all agents into a single instruction.md"""
from pathlib import Path

def merge_agent_docs(agent_dir: Path) -> None:
    """Merge instruction.md and examples.md for a single agent."""
    instruction_file = agent_dir / "instruction.md"
    examples_file = agent_dir / "examples.md"

    if not instruction_file.exists() or not examples_file.exists():
        print(f"Skipping {agent_dir.name}: missing files")
        return

    # Read both files
    instruction_content = instruction_file.read_text()
    examples_content = examples_file.read_text()

    # Remove trailing markers if they exist
    instruction_content = instruction_content.replace("# END OF INSTRUCTIONS", "").rstrip()
    examples_content = examples_content.replace("# END OF EXAMPLES", "").rstrip()

    # Merge: instructions first, then examples
    merged_content = f"{instruction_content}\n\n---\n\n{examples_content}\n"

    # Write merged content back to instruction.md
    instruction_file.write_text(merged_content)

    # Delete examples.md (we'll keep a backup by renaming)
    backup_file = agent_dir / "examples.md.bak"
    examples_file.rename(backup_file)

    print(f"✓ Merged {agent_dir.name}/instruction.md (examples.md → examples.md.bak)")

def main():
    """Merge all agent instruction and example files."""
    project_root = Path(__file__).parent.parent
    agents_dir = project_root / "agents"

    # Find all agent directories with both files
    for agent_dir in sorted(agents_dir.iterdir()):
        if not agent_dir.is_dir():
            continue
        if agent_dir.name.startswith(".") or agent_dir.name == "__pycache__":
            continue

        merge_agent_docs(agent_dir)

    print("\nDone! All agent docs merged.")
    print("To restore examples.md files, rename .bak files back")

if __name__ == "__main__":
    main()
