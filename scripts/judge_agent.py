
#!/usr/bin/env python3
"""Run an agent on its evaluation set and score each answer with an LLM judge."""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

import google.generativeai as genai

# Ensure project root is on sys.path so `agents` package can be imported
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from google.adk.agents.llm_agent import Agent as AdkAgent
from google.adk.runners import InMemoryRunner
from google.genai import types

# Import SessionManager and SessionMemory for context management
try:
    from session_manager import SessionManager, SessionMemory
    HAS_SESSION_MANAGER = True
except ImportError:
    HAS_SESSION_MANAGER = False
    print("Warning: Could not import SessionManager. Session context will not be available.")

# Try to import onboarding agent's business card parser for validation
try:
    import importlib.util
    parser_path = PROJECT_ROOT / "agents" / "onboarding-agent" / "parser.py"
    if parser_path.exists():
        spec = importlib.util.spec_from_file_location("onboarding_parser", parser_path)
        parser_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(parser_module)
        extract_business_card_from_response = parser_module.extract_business_card_from_response
        HAS_BUSINESS_CARD_PARSER = True
    else:
        HAS_BUSINESS_CARD_PARSER = False
except Exception as e:
    HAS_BUSINESS_CARD_PARSER = False
    print(f"Warning: Could not import business card parser: {e}")

# ---------------------------------------------------------------------------
# Environment loading
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# Environment loading
# ---------------------------------------------------------------------------

def load_project_env() -> None:
    """Load key/value pairs from the project's .env if GEMINI_API_KEY not already set."""
    env_path = PROJECT_ROOT / ".env"
    if "GEMINI_API_KEY" in os.environ or not env_path.exists():
        return
    with open(env_path, "r") as env_file:
        for line in env_file:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())


def _case_input_to_prompt(case_input: Any) -> str:
    """Convert structured case input to a user-facing prompt string."""
    if isinstance(case_input, dict):
        user_request = case_input.get("user_request")
        if isinstance(user_request, str) and user_request.strip():
            return user_request.strip()
        return json.dumps(case_input, indent=2, ensure_ascii=False)
    return str(case_input)


def _content_to_text(content: types.Content | None) -> str:
    if not content or not content.parts:
        return ""
    texts: List[str] = []
    for part in content.parts:
        if getattr(part, "text", None):
            texts.append(part.text)
    return "\n".join(texts).strip()


def _ensure_session(runner: InMemoryRunner, user_id: str, session_id: str) -> None:
    """Create a session if it doesn't already exist."""
    session_service = runner.session_service
    if hasattr(session_service, "get_session_sync"):
        existing = session_service.get_session_sync(
            app_name=runner.app_name, user_id=user_id, session_id=session_id
        )
    else:
        existing = None
    if existing:
        return
    if hasattr(session_service, "create_session_sync"):
        session_service.create_session_sync(
            app_name=runner.app_name, user_id=user_id, session_id=session_id
        )
    else:
        raise RuntimeError("Session service does not support sync session creation.")

# ---------------------------------------------------------------------------
# CLI parsing
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--agent-dir",
        type=Path,
        required=True,
        help="Path to the agent directory (contains agent.py and evaluation/test.json).",
    )
    parser.add_argument(
        "--tests",
        type=Path,
        help="Optional path to a test.json file; defaults to <agent-dir>/evaluation/test.json.",
    )
    parser.add_argument(
        "--max-cases",
        type=int,
        default=None,
        help="Optional cap on number of test cases to run.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Skip invoking the target agent (useful when you just want to preview prompts).",
    )
    return parser.parse_args()

# ---------------------------------------------------------------------------
# Agent loading
# ---------------------------------------------------------------------------

def load_agent(agent_dir: Path) -> AdkAgent:
    """Dynamically import agent.py and return the first exported Agent instance."""
    spec = importlib.util.spec_from_file_location("target_agent", agent_dir / "agent.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[attr-defined]
    for value in vars(module).values():
        if isinstance(value, AdkAgent):
            return value
    raise RuntimeError(f"No google.adk Agent instance found in {agent_dir}/agent.py")

# ---------------------------------------------------------------------------
# Running the agent (replace this stub with your preferred ADK runner)
# ---------------------------------------------------------------------------

def run_agent_case(agent: AdkAgent, case_input: Dict[str, Any], session_context: Dict[str, Any] | None = None) -> str:
    """Invoke the agent via an in-memory runner and return the final text output.

    Args:
        agent: The agent to run
        case_input: The test case input (user message or structured input)
        session_context: Optional session context with business_card, conversation history, etc.
    """
    runner = InMemoryRunner(agent=agent)
    user_id = "judge_user"
    session_id = f"judge_session_{uuid.uuid4().hex}"
    _ensure_session(runner, user_id, session_id)

    # Prepare the message text
    message_text = _case_input_to_prompt(case_input)

    # If session context is provided, prepend it to the message as system context
    # This simulates what the orchestrator/server would provide to the agent
    if session_context:
        context_parts = ["SESSION CONTEXT:"]
        if "business_card" in session_context and session_context["business_card"] is not None:
            bc = session_context["business_card"]
            context_parts.append(f"Business Card (from shared context):")
            context_parts.append(json.dumps(bc, indent=2))
            print(f"  [Providing business_card in context: {bc.get('name', 'N/A')}]")

        for key, value in session_context.items():
            if key != "business_card" and value is not None:
                context_parts.append(f"{key}: {value}")
                print(f"  [Providing {key} in context]")

        context_parts.append("")  # Empty line before user message
        context_parts.append("USER MESSAGE:")

        # Prepend context to the actual user message
        message_text = "\n".join(context_parts) + "\n" + message_text
    new_message = types.Content(
        role="user",
        parts=[types.Part(text=message_text)],
    )

    final_response: str | None = None
    all_responses: List[str] = []
    function_calls: List[str] = []
    function_responses: List[str] = []
    event_count = 0
    event_authors: List[str] = []
    # Track responses by author to capture sub-agent outputs
    responses_by_author: Dict[str, List[str]] = {}

    for event in runner.run(
        user_id=user_id,
        session_id=session_id,
        new_message=new_message,
    ):
        event_count += 1
        
        # Debug: log event details
        event_author = getattr(event, 'author', None)
        if event_author:
            event_authors.append(event_author)
        is_final = event.is_final_response() if hasattr(event, 'is_final_response') else False
        
        # Debug: print event structure for first few events
        if event_count <= 3:
            print(f"  [DEBUG] Event #{event_count}: author={event_author}, is_final={is_final}, "
                  f"has_content={bool(event.content)}, has_parts={bool(event.content and event.content.parts)}")
            if event.content and event.content.parts:
                for i, part in enumerate(event.content.parts):
                    part_attrs = [attr for attr in dir(part) if not attr.startswith('_')]
                    print(f"    Part {i} attributes: {[a for a in part_attrs if 'call' in a.lower() or 'tool' in a.lower()]}")
        
        # Collect all agent responses (including from sub-agents)
        candidate = _content_to_text(event.content)
        if candidate:
            all_responses.append(candidate)
            # Track responses by author
            if event_author:
                if event_author not in responses_by_author:
                    responses_by_author[event_author] = []
                responses_by_author[event_author].append(candidate)

        # Capture function calls (for orchestrator agents)
        # Check multiple ways function calls might appear in events
        if event.content and event.content.parts:
            for part in event.content.parts:
                # Check for function_call attribute
                if hasattr(part, 'function_call') and part.function_call:
                    fc_name = getattr(part.function_call, 'name', None)
                    if fc_name:
                        function_calls.append(fc_name)
                        print(f"  [DEBUG] Found function_call: {fc_name}")
                
                # Check for function_response attribute (tool execution results)
                if hasattr(part, 'function_response') and part.function_response:
                    fr_name = getattr(part.function_response, 'name', None)
                    if fr_name:
                        function_responses.append(fr_name)
                        print(f"  [DEBUG] Found function_response: {fr_name}")
        
        # Also check event-level attributes for function calls
        if hasattr(event, 'function_call') and event.function_call:
            fc_name = getattr(event.function_call, 'name', None)
            if fc_name:
                function_calls.append(fc_name)
                print(f"  [DEBUG] Found event-level function_call: {fc_name}")
        
        # Check for tool invocations in event metadata
        if hasattr(event, 'tool_calls'):
            for tool_call in event.tool_calls:
                if hasattr(tool_call, 'name'):
                    function_calls.append(tool_call.name)
                    print(f"  [DEBUG] Found tool_call: {tool_call.name}")
        
        # Track final response from the root agent
        if event_author == agent.name and is_final:
            if candidate:
                final_response = candidate

    # Debug: log what we collected
    if event_count == 0:
        raise RuntimeError("No events were emitted by the agent runner. This suggests the agent failed to start or encountered an error.")
    
    # For orchestrator agents: if we see responses from sub-agents, that means tools were called
    # Sub-agents have names like 'onboarding_agent', 'frontdesk_agent', etc.
    # The root agent is named 'root_agent'
    sub_agent_names = ['onboarding_agent', 'frontdesk_agent', 'creator_finder_agent', 
                       'campaign_brief_agent', 'outreach_message_agent', 'campaign_builder_agent']
    sub_agent_responses = [author for author in event_authors if author in sub_agent_names]
    
    # Collect sub-agent response text if available
    sub_agent_texts: List[str] = []
    for sub_agent_name in sub_agent_names:
        if sub_agent_name in responses_by_author:
            sub_agent_texts.extend(responses_by_author[sub_agent_name])
    
    # Return best available output (prioritize actual responses over metadata)
    # For orchestrator agents: if we have function calls OR sub-agent responses, 
    # return the actual sub-agent output text (not just a description)
    if final_response:
        return final_response
    elif all_responses:
        # If we have responses, return them (this includes sub-agent responses)
        return "\n".join(all_responses)
    elif sub_agent_texts:
        # If we detected sub-agent responses, return them as evidence of tool calls
        return "\n".join(sub_agent_texts)
    elif function_calls or function_responses:
        # If we detected function calls but no text responses, 
        # return a description (this is a fallback for when tool calls don't produce visible text)
        calls = function_calls if function_calls else function_responses
        return f"[ORCHESTRATOR] Called tools: {', '.join(calls)}"
    elif sub_agent_responses:
        # Fallback: if we saw sub-agent activity but no text, that's still evidence of tool calls
        return f"[ORCHESTRATOR] Delegated to: {', '.join(sub_agent_responses)}"
    else:
        # If we got events but no output, the agent may have completed without producing anything
        # Return a minimal response to allow the judge to evaluate the behavior
        if event_count > 0:
            return f"[ORCHESTRATOR] Agent completed with no output. Events: {event_count}, Authors: {', '.join(event_authors) if event_authors else 'none'}"
        # Provide more context in the error
        raise RuntimeError(
            f"Agent produced no text response or function calls for the given input. "
            f"Events received: {event_count}, Authors seen: {event_authors}, "
            f"Agent name: {agent.name}"
        )

# ---------------------------------------------------------------------------
# LLM judge
# ---------------------------------------------------------------------------

@dataclass
class JudgeResult:
    score: float
    rationale: str

class Judge:
    """Simple wrapper around Gemini for scoring agent responses."""

    def __init__(self, model_name: str = "gemini-2.5-flash") -> None:
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError("Set GEMINI_API_KEY (or GOOGLE_API_KEY) before running the judge.")
        genai.configure(api_key=api_key)
        self._model = genai.GenerativeModel(model_name)
        self._last_request_time = 0.0
        self._min_request_interval = 6.5  # ~9 requests per minute to stay under 10/min limit

    def score(
        self,
        case_description: str,
        expected_output_type: str,
        test_input: Dict[str, Any],
        agent_output: str,
        expected_behavior: Dict[str, Any] | None = None,
        agent_instructions: str | None = None,
    ) -> JudgeResult:
        # Rate limiting: ensure we don't exceed API quota
        elapsed = time.time() - self._last_request_time
        if elapsed < self._min_request_interval:
            sleep_time = self._min_request_interval - elapsed
            print(f"  [Rate limiting: waiting {sleep_time:.1f}s...]", end="\r")
            time.sleep(sleep_time)

        # Build the evaluation prompt
        prompt_parts = [
            "You are an impartial judge scoring how well an agent handled a test case.",
            "",
            f"Test description: {case_description}",
            f"Expected output type: {expected_output_type}",
            f"Structured input (JSON):",
            json.dumps(test_input, indent=2, ensure_ascii=False),
        ]

        # Add agent instructions if available
        if agent_instructions:
            prompt_parts.extend([
                "",
                "Agent Instructions (the agent must follow these):",
                agent_instructions.strip(),
            ])

        # Add expected behavior if available
        if expected_behavior:
            prompt_parts.extend([
                "",
                "Expected behavior (the agent should exhibit these behaviors):",
                json.dumps(expected_behavior, indent=2, ensure_ascii=False),
            ])

        prompt_parts.extend([
            "",
            "Agent output:",
            agent_output.strip(),
            "",
            "Evaluate the agent's response based on:",
            "1. Does it follow the agent instructions?",
            "2. Does it exhibit the expected behavior?",
            "3. Does it produce the expected output type?",
            "4. Is the response appropriate for the given input?",
            "",
            "Score the response on a 0-1 confidence scale where:",
            "- 1.0 = perfectly satisfies all expectations and follows instructions.",
            "- 0.0 = fails entirely or violates critical instructions.",
            'Respond ONLY with a JSON object: {"score": <float 0-1>, "rationale": "<1-2 sentence reason>"}.',
        ])

        prompt = "\n".join(prompt_parts)
        # Try up to 3 times to get valid JSON
        for attempt in range(3):
            try:
                self._last_request_time = time.time()
                response = self._model.generate_content(prompt, generation_config={"temperature": 0.1})
                raw = response.text.strip()

                # Try to extract JSON if wrapped in markdown code blocks
                if raw.startswith("```"):
                    lines = raw.split("\n")
                    # Remove first and last lines (markdown fences)
                    raw = "\n".join(lines[1:-1]) if len(lines) > 2 else raw
                    # Remove json language identifier if present
                    if raw.startswith("json"):
                        raw = raw[4:].strip()

                payload = json.loads(raw)
                return JudgeResult(score=float(payload["score"]), rationale=str(payload["rationale"]))
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                if attempt == 2:  # Last attempt
                    # Return a default low score if we can't parse
                    print(f"Warning: Failed to parse judge response after 3 attempts. Raw: {raw[:100]}")
                    return JudgeResult(score=0.0, rationale=f"Judge failed to provide valid score (parse error: {str(e)})")
                continue  # Retry

        # Fallback (shouldn't reach here)
        return JudgeResult(score=0.0, rationale="Judge failed to provide valid score")

# ---------------------------------------------------------------------------
# High-level orchestration
# ---------------------------------------------------------------------------

def load_cases(test_path: Path) -> List[Dict[str, Any]]:
    with open(test_path, "r") as fh:
        return json.load(fh)


def load_agent_instructions(agent_dir: Path) -> str | None:
    """Load the agent's instruction.md file if it exists."""
    instruction_path = agent_dir / "instruction.md"
    if instruction_path.exists():
        with open(instruction_path, "r") as fh:
            return fh.read()
    return None


def main() -> None:
    # Ensure env vars from project .env are available (including GEMINI_API_KEY)
    load_project_env()
    args = parse_args()
    test_path = args.tests or (args.agent_dir / "evaluation" / "test.json")
    cases = load_cases(test_path)
    if args.max_cases:
        cases = cases[: args.max_cases]

    agent = load_agent(args.agent_dir)
    agent_instructions = load_agent_instructions(args.agent_dir)
    judge = Judge()

    total_score = 0.0
    table: List[Tuple[str, float, str]] = []

    for idx, case in enumerate(cases, start=1):
        # Support different test case formats
        # Format 1: onboarding/frontdesk format with user_message and session_context
        # Format 2: regular format with input and expected_output_type
        if "user_message" in case:
            case_input = {"user_request": case["user_message"]}
            session_context = case.get("session_context")
        else:
            case_input = case["input"]
            session_context = case.get("session_context")

        # Support both expected_output_type (for regular agents) and expected_redirect (for orchestrator)
        expected = case.get("expected_output_type") or case.get("expected_redirect", "unspecified")
        if isinstance(expected, list):
            expected = f"redirect to agents: {', '.join(expected)}"
        elif expected and expected != "unspecified":
            expected = f"redirect to: {expected}" if "expected_redirect" in case else expected
        description = case.get("description", f"Case #{idx}")
        expected_behavior = case.get("expected_behavior")

        if args.dry_run:
            print(f"[{idx}/{len(cases)}] {description} -> skipped (dry-run)")
            continue

        print(f"[{idx}/{len(cases)}] Running: {description}")
        agent_output = run_agent_case(agent, case_input, session_context)

        # Validate business card extraction if expected
        business_card_validated = True
        business_card_validation_msg = ""
        if HAS_BUSINESS_CARD_PARSER and expected_behavior:
            if expected_behavior.get("should_generate_confirmation_block"):
                parsed = extract_business_card_from_response(agent_output)
                if parsed["has_confirmation"]:
                    print(f"  ✓ Business card confirmation block found and parsed")
                    if parsed["business_card"]:
                        bc = parsed["business_card"]
                        print(f"    Name: {bc.name}, Location: {bc.location}, Service: {bc.service_type}")
                else:
                    business_card_validated = False
                    business_card_validation_msg = " [WARNING: No business card confirmation block found in output]"
                    print(f"  ✗ Business card confirmation block NOT found (expected)")

        result = judge.score(
            description,
            expected,
            case_input,
            agent_output,
            expected_behavior=expected_behavior,
            agent_instructions=agent_instructions,
        )

        # Apply penalty if business card validation failed
        final_score = result.score
        if not business_card_validated:
            final_score = min(result.score, 0.5)  # Cap at 0.5 if business card not generated
            result = JudgeResult(
                score=final_score,
                rationale=result.rationale + business_card_validation_msg
            )

        total_score += final_score
        table.append((description, final_score, result.rationale))
        print(f"[{idx}/{len(cases)}] {description} -> {final_score:.2f} ({result.rationale})")

    if table:
        avg_score = total_score / len(table)
        print(f"\nAverage confidence score: {avg_score:.3f}")
        print("Detailed results:")
        for desc, score, rationale in table:
            print(f"- {desc}: {score:.2f} | {rationale}")

        # Save report to evaluation folder
        report_data = {
            "average_confidence_score": round(avg_score, 3),
            "total_cases": len(table),
            "test_results": [
                {
                    "description": desc,
                    "score": round(score, 2),
                    "rationale": rationale
                }
                for desc, score, rationale in table
            ]
        }

        report_path = args.agent_dir / "evaluation" / "report.json"
        with open(report_path, "w") as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        print(f"\n✓ Report saved to: {report_path}")
    else:
        print("\nDry-run complete. No scores generated.")


if __name__ == "__main__":
    main()
