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
import re
import google.generativeai as genai
import os
import requests

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).resolve().parent.parent))
from agents.utils import AgentName, load_agent_env

# Configure Gemini if key is present (used when backend=gemini)
load_agent_env(AgentName.ONBOARDING_AGENT)  # Load any agent env to get API key
if os.environ.get("GOOGLE_API_KEY"):
    genai.configure(api_key=os.environ["GOOGLE_API_KEY"])


def _call_gemini(prompt: str, model_name: str) -> str:
    model = genai.GenerativeModel(model_name)
    response = model.generate_content(
        prompt,
        generation_config=genai.types.GenerationConfig(
            temperature=0.7,  # Some creativity for diverse tests
            top_p=0.9,
            max_output_tokens=8000,
        )
    )
    return response.text.strip()


def _extract_json_array(response_text: str) -> Optional[List[Any]]:
    """Try to extract a JSON array from the LLM response."""
    # Direct parse
    try:
        parsed = json.loads(response_text)
        if isinstance(parsed, list):
            return parsed
        if isinstance(parsed, dict):
            return [parsed]
    except Exception:
        pass

    # Strip code fences if still present
    if response_text.startswith("```"):
        lines = response_text.split("\n")
        content = "\n".join(lines[1:-1]) if len(lines) > 2 else response_text
        if content.startswith("json"):
            content = content[4:].strip()
        try:
            parsed = json.loads(content)
            if isinstance(parsed, list):
                return parsed
            if isinstance(parsed, dict):
                return [parsed]
        except Exception:
            pass

    # Regex fallback: first JSON array OR object substring
    match = re.search(r"(\[.*\]|\{.*\})", response_text, re.DOTALL)
    if match:
        candidate = match.group(0)
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, list):
                return parsed
            if isinstance(parsed, dict):
                return [parsed]
        except Exception:
            pass
    return None


def _call_openai_compatible(
    prompt: str,
    model_name: str,
    api_base: str,
    api_key: Optional[str],
    max_tokens: int,
) -> str:
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    resp = requests.post(
        f"{api_base}/chat/completions",
        headers=headers,
        json={
            "model": model_name,
            "temperature": 0.7,
            "top_p": 0.9,
            "max_tokens": max_tokens,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": "You are a test case generator that outputs STRICT JSON arrays."},
                {"role": "user", "content": prompt},
            ],
            "metadata": {"source": "generate_tests_with_llm"},
        },
        timeout=300,
    )
    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"].strip()


def generate_tests_with_llm(
    agent_dir: Path,
    num_tests: int = 15,
    backend: str = "gemini",
    model: Optional[str] = None,
    api_base: Optional[str] = None,
    api_key: Optional[str] = None,
    max_tokens: int = 2000,
) -> List[Dict[str, Any]]:
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

    # Choose backend and generate
    try:
        backend_choice = backend
        if backend_choice == "gemini":
            model_name = model or "gemini-2.5-flash"
            response_text = _call_gemini(prompt, model_name)
        else:
            model_name = model or os.environ.get("LLM_GEN_MODEL", "llama3.1")
            base = api_base or os.environ.get("LLM_GEN_BASE_URL", "http://localhost:11434/v1")
            key = api_key or os.environ.get("LLM_GEN_API_KEY")
            max_toks = max_tokens or int(os.environ.get("LLM_GEN_MAX_TOKENS", "2000"))
            response_text = _call_openai_compatible(prompt, model_name, base, key, max_toks)

        # Remove markdown code blocks if present
        if response_text.startswith('```'):
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

        # Parse JSON array, with fallbacks
        test_cases = _extract_json_array(response_text)

        if not isinstance(test_cases, list):
            snippet = response_text[:400].replace("\n", " ")
            print(f"Error: LLM did not return a JSON array. Snippet: {snippet}")
            return []

        print(f"✓ Generated {len(test_cases)} test cases using {backend_choice}")
        return test_cases

    except json.JSONDecodeError as e:
        print(f"Error: Failed to parse LLM response as JSON: {e}")
        print(f"Response was: {response_text[:500]}")
        return []
    except Exception as e:
        print(f"Error generating tests with LLM ({backend_choice}): {e}")
        return []


def get_golden_tests(agent_name: str) -> List[Dict[str, Any]]:
    """Get golden hardcoded tests from test_utils.py."""
    try:
        # Import test_utils to get hardcoded golden tests
        sys.path.insert(0, str(Path(__file__).parent.parent / "agents"))
        import test_utils

        # Map agent folder name to enum value (directories now use underscores)
        agent_enum_map = {
            "onboarding_agent": "onboarding_agent",
            "frontdesk_agent": "frontdesk_agent",
            "creator_finder_agent": "creator_finder_agent",
            "campaign_brief_agent": "campaign_brief_agent",
            "outreach_message_agent": "outreach_message_agent",
            "campaign_builder_agent": "campaign_builder_agent",
            "orchestrator_agent": "root_agent"
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
    backend = os.environ.get("LLM_GEN_BACKEND", "gemini")
    backend_model = os.environ.get("LLM_GEN_MODEL")
    backend_base = os.environ.get("LLM_GEN_BASE_URL")
    backend_key = os.environ.get("LLM_GEN_API_KEY")
    backend_max_tokens = int(os.environ.get("LLM_GEN_MAX_TOKENS", "2000"))
    target_llm = int(os.environ.get("LLM_GEN_TARGET_TESTS", "10"))
    max_attempts = int(os.environ.get("LLM_GEN_MAX_ATTEMPTS", "3"))

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
            used_names = {test["name"] for test in golden_tests if "name" in test}

            llm_tests: List[Dict[str, Any]] = []
            attempts = 0
            while len(llm_tests) < target_llm and attempts < max_attempts:
                needed = target_llm - len(llm_tests)
                batch_size = max(needed, target_llm)
                batch = generate_tests_with_llm(
                    agent_dir,
                    num_tests=batch_size,
                    backend=backend,
                    model=backend_model,
                    api_base=backend_base,
                    api_key=backend_key,
                    max_tokens=backend_max_tokens,
                )
                added = 0
                for test in batch:
                    name = test.get("name")
                    if not name or name in used_names:
                        continue
                    llm_tests.append(test)
                    used_names.add(name)
                    added += 1
                    if len(llm_tests) >= target_llm:
                        break
                if added == 0:
                    break
                attempts += 1
            if len(llm_tests) < target_llm:
                print(f"  Warning: only collected {len(llm_tests)} LLM tests (target {target_llm}).")

            # Merge them
            test_cases = merge_tests(golden_tests, llm_tests)
            print(f"  ✓ Combined {len(golden_tests)} golden + {len(llm_tests)} LLM = {len(test_cases)} total tests")
        else:
            print("  Mode: LLM-only")
            llm_tests: List[Dict[str, Any]] = []
            used_names: set[str] = set()
            attempts = 0
            while len(llm_tests) < target_llm and attempts < max_attempts:
                needed = target_llm - len(llm_tests)
                batch_size = max(needed, target_llm)
                batch = generate_tests_with_llm(
                    agent_dir,
                    num_tests=batch_size,
                    backend=backend,
                    model=backend_model,
                    api_base=backend_base,
                    api_key=backend_key,
                    max_tokens=backend_max_tokens,
                )
                added = 0
                for test in batch:
                    name = test.get("name")
                    if not name or name in used_names:
                        continue
                    llm_tests.append(test)
                    used_names.add(name)
                    added += 1
                    if len(llm_tests) >= target_llm:
                        break
                if added == 0:
                    break
                attempts += 1
            if len(llm_tests) < target_llm:
                print(f"  Warning: only collected {len(llm_tests)} LLM tests (target {target_llm}).")
            test_cases = llm_tests

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
            "onboarding_agent",
            "frontdesk_agent",
            "creator_finder_agent",
            "campaign_brief_agent",
            "outreach_message_agent",
            "campaign_builder_agent",
            "orchestrator_agent"
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
                llm_tests = generate_tests_with_llm(
                    agent_dir,
                    num_tests=10,
                    backend=backend,
                    model=backend_model,
                    api_base=backend_base,
                    api_key=backend_key,
                    max_tokens=backend_max_tokens,
                )
                test_cases = merge_tests(golden_tests, llm_tests)
                print(f"  ✓ Combined {len(golden_tests)} golden + {len(llm_tests)} LLM = {len(test_cases)} total tests")
            else:
                print("  Mode: LLM-only")
                test_cases = generate_tests_with_llm(
                    agent_dir,
                    num_tests=15,
                    backend=backend,
                    model=backend_model,
                    api_base=backend_base,
                    api_key=backend_key,
                    max_tokens=backend_max_tokens,
                )

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
