"""LLM-based test case generator for agents.

This script reads an agent's instruction.md and examples.md files and uses
an LLM to generate diverse, comprehensive test cases automatically.

Supports two modes:
1. LLM-only: Generate tests purely from LLM
2. Hybrid: Combine golden hardcoded tests + LLM-generated tests
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
import google.generativeai as genai
import os

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).resolve().parent.parent))
from agents.utils import AgentName, load_agent_env

# Configure Gemini
load_agent_env(AgentName.ONBOARDING_AGENT)  # Load any agent env to get API key
genai.configure(api_key=os.environ['GOOGLE_API_KEY'])


def generate_tests_with_llm(agent_dir: Path, num_tests: int = 15) -> List[Dict[str, Any]]:
    """Generate test cases for an agent using LLM."""

    # Read instruction and examples files
    instruction_file = agent_dir / "instruction.md"
    examples_file = agent_dir / "examples.md"

    if not instruction_file.exists():
        print(f"Warning: {instruction_file} not found")
        return []

    instruction_content = instruction_file.read_text()
    examples_content = examples_file.read_text() if examples_file.exists() else "No examples provided."

    # Create prompt for LLM
    prompt = f"""You are a test case generator for AI agents. Your task is to generate comprehensive, diverse test cases in JSON format.

# AGENT INSTRUCTIONS:
{instruction_content}

# AGENT EXAMPLES:
{examples_content}

# YOUR TASK:
Generate {num_tests} diverse test cases in JSON array format. Each test case should:

1. Test different scenarios (happy path, edge cases, error handling, clarifications, corrections, etc.)
2. Cover all functionality mentioned in the instructions
3. Include challenging scenarios that might break the agent
4. Test boundary conditions and unusual inputs
5. Ensure diversity - don't repeat similar scenarios

# REQUIRED JSON FORMAT:
Output ONLY a valid JSON array with this structure:

[
  {{
    "name": "snake_case_test_name",
    "description": "Clear description of what this test validates",
    "user_message": "The exact user input message",
    "session_context": {{
      "business_card": null,  // or object with business card data if applicable
      "workflow_state": {{}},  // optional workflow state
      "last_agent_message": ""  // optional, if testing follow-up
    }},
    "expected_behavior": {{
      "should_do_x": true,
      "should_not_do_y": true,
      // Use descriptive boolean flags for behaviors
    }},
    "expected_response_contains": ["keyword1", "keyword2"],  // optional
    "expected_business_card": {{}}  // optional, if agent should generate business card
  }}
]

CRITICAL:
- Output ONLY valid JSON, no markdown, no explanations, no code blocks
- Ensure all strings are properly escaped
- Use null (not None) for null values
- Test names must be unique and descriptive
- Cover edge cases from the examples

Generate the {num_tests} test cases now:"""

    # Call Gemini to generate tests
    model = genai.GenerativeModel('gemini-2.0-flash-exp')

    try:
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.7,  # Some creativity for diverse tests
                top_p=0.9,
                max_output_tokens=8000,
            )
        )

        # Extract JSON from response
        response_text = response.text.strip()

        # Remove markdown code blocks if present
        if response_text.startswith('```'):
            # Find the actual JSON content
            lines = response_text.split('\n')
            json_lines = []
            in_json = False
            for line in lines:
                if line.startswith('```'):
                    in_json = not in_json
                    continue
                if in_json or (not line.startswith('```')):
                    json_lines.append(line)
            response_text = '\n'.join(json_lines).strip()

        # Parse JSON
        test_cases = json.loads(response_text)

        if not isinstance(test_cases, list):
            print(f"Error: LLM did not return a JSON array")
            return []

        print(f"✓ Generated {len(test_cases)} test cases using LLM")
        return test_cases

    except json.JSONDecodeError as e:
        print(f"Error: Failed to parse LLM response as JSON: {e}")
        print(f"Response was: {response_text[:500]}")
        return []
    except Exception as e:
        print(f"Error generating tests with LLM: {e}")
        return []


def get_golden_tests(agent_name: str) -> List[Dict[str, Any]]:
    """Get golden hardcoded tests from test_utils.py."""
    try:
        # Import test_utils to get hardcoded golden tests
        sys.path.insert(0, str(Path(__file__).parent.parent / "agents"))
        import test_utils

        # Map agent folder name to enum value
        agent_enum_map = {
            "onboarding-agent": "onboarding_agent",
            "frontdesk-agent": "frontdesk_agent",
            "creator-finder-agent": "creator_finder_agent",
            "campaign-brief-agent": "campaign_brief_agent",
            "outreach-message-agent": "outreach_message_agent",
            "campaign-builder-agent": "campaign_builder_agent",
            "orchestrator-agent": "root_agent"
        }

        enum_value = agent_enum_map.get(agent_name)
        if not enum_value:
            return []

        # Get the generator function
        generators = test_utils.AGENT_TEST_GENERATORS
        if enum_value in generators:
            golden_tests = generators[enum_value]()
            print(f"  ✓ Loaded {len(golden_tests)} golden tests from test_utils.py")
            return golden_tests

        return []
    except Exception as e:
        print(f"  Warning: Could not load golden tests: {e}")
        return []


def merge_tests(golden_tests: List[Dict[str, Any]], llm_tests: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Merge golden and LLM tests, avoiding duplicates by name."""
    # Start with all golden tests
    merged = list(golden_tests)
    golden_names = {test['name'] for test in golden_tests}

    # Add LLM tests that don't duplicate golden test names
    for llm_test in llm_tests:
        if llm_test['name'] not in golden_names:
            merged.append(llm_test)
        else:
            print(f"  Skipping duplicate LLM test: {llm_test['name']}")

    return merged


def main():
    """Generate tests for all agents or a specific agent."""
    # Check for --hybrid flag
    hybrid_mode = "--hybrid" in sys.argv
    if hybrid_mode:
        sys.argv.remove("--hybrid")

    if len(sys.argv) > 1:
        # Generate for specific agent
        agent_name = sys.argv[1]
        agent_dir = Path(__file__).parent.parent / "agents" / agent_name

        if not agent_dir.exists():
            print(f"Error: Agent directory not found: {agent_dir}")
            sys.exit(1)

        print(f"Generating tests for {agent_name}...")

        if hybrid_mode:
            print("  Mode: HYBRID (golden + LLM tests)")
            # Get golden tests
            golden_tests = get_golden_tests(agent_name)

            # Generate LLM tests
            llm_tests = generate_tests_with_llm(agent_dir, num_tests=10)  # Fewer LLM tests since we have golden

            # Merge them
            test_cases = merge_tests(golden_tests, llm_tests)
            print(f"  ✓ Combined {len(golden_tests)} golden + {len(llm_tests)} LLM = {len(test_cases)} total tests")
        else:
            print("  Mode: LLM-only")
            test_cases = generate_tests_with_llm(agent_dir, num_tests=15)

        if test_cases:
            # Save to evaluation/test.json
            eval_dir = agent_dir / "evaluation"
            eval_dir.mkdir(exist_ok=True)

            test_file = eval_dir / "test.json"
            test_file.write_text(json.dumps(test_cases, indent=2))
            print(f"✓ Saved {len(test_cases)} test cases to {test_file}")
        else:
            print(f"✗ No test cases generated")
            sys.exit(1)
    else:
        # Generate for all testable agents
        agents_dir = Path(__file__).parent.parent / "agents"

        testable_agents = [
            "onboarding-agent",
            "frontdesk-agent",
            "creator-finder-agent",
            "campaign-brief-agent",
            "outreach-message-agent",
            "campaign-builder-agent",
            "orchestrator-agent"
        ]

        for agent_name in testable_agents:
            agent_dir = agents_dir / agent_name
            if not agent_dir.exists():
                print(f"Skipping {agent_name} (not found)")
                continue

            print(f"\nGenerating tests for {agent_name}...")

            if hybrid_mode:
                print("  Mode: HYBRID (golden + LLM tests)")
                golden_tests = get_golden_tests(agent_name)
                llm_tests = generate_tests_with_llm(agent_dir, num_tests=10)
                test_cases = merge_tests(golden_tests, llm_tests)
                print(f"  ✓ Combined {len(golden_tests)} golden + {len(llm_tests)} LLM = {len(test_cases)} total tests")
            else:
                print("  Mode: LLM-only")
                test_cases = generate_tests_with_llm(agent_dir, num_tests=15)

            if test_cases:
                eval_dir = agent_dir / "evaluation"
                eval_dir.mkdir(exist_ok=True)

                test_file = eval_dir / "test.json"
                test_file.write_text(json.dumps(test_cases, indent=2))
                print(f"✓ Saved {len(test_cases)} test cases to {test_file}")
            else:
                print(f"✗ Failed to generate tests for {agent_name}")


if __name__ == "__main__":
    main()
