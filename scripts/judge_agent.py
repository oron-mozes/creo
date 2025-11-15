
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

def run_agent_case(agent: AdkAgent, case_input: Dict[str, Any]) -> str:
    """Invoke the agent via an in-memory runner and return the final text output."""
    runner = InMemoryRunner(agent=agent)
    user_id = "judge_user"
    session_id = f"judge_session_{uuid.uuid4().hex}"
    _ensure_session(runner, user_id, session_id)

    message_text = _case_input_to_prompt(case_input)
    new_message = types.Content(
        role="user",
        parts=[types.Part(text=message_text)],
    )

    final_response: str | None = None
    all_responses: List[str] = []
    function_calls: List[str] = []

    for event in runner.run(
        user_id=user_id,
        session_id=session_id,
        new_message=new_message,
    ):
        # Collect all agent responses (including from sub-agents)
        candidate = _content_to_text(event.content)
        if candidate:
            all_responses.append(candidate)

        # Capture function calls (for orchestrator agents)
        if event.content and event.content.parts:
            for part in event.content.parts:
                if hasattr(part, 'function_call') and part.function_call:
                    fc_name = getattr(part.function_call, 'name', None)
                    if fc_name:
                        function_calls.append(fc_name)

        # Track final response from the root agent
        if event.author == agent.name and event.is_final_response():
            if candidate:
                final_response = candidate

    # Return best available output
    if final_response:
        return final_response
    elif all_responses:
        return "\n".join(all_responses)
    elif function_calls:
        # For orchestrator agents that only make function calls
        return f"Agent delegated to: {', '.join(function_calls)}"
    else:
        raise RuntimeError("Agent produced no text response or function calls for the given input.")
    return final_response

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
    ) -> JudgeResult:
        # Rate limiting: ensure we don't exceed API quota
        elapsed = time.time() - self._last_request_time
        if elapsed < self._min_request_interval:
            sleep_time = self._min_request_interval - elapsed
            print(f"  [Rate limiting: waiting {sleep_time:.1f}s...]", end="\r")
            time.sleep(sleep_time)

        prompt = f"""
You are an impartial judge scoring how well an agent handled a test case.

Test description: {case_description}
Expected output type: {expected_output_type}
Structured input (JSON):
{json.dumps(test_input, indent=2, ensure_ascii=False)}

Agent output:
{agent_output.strip()}

Score the response on a 0-1 confidence scale where:
- 1.0 = perfectly satisfies the expectations.
- 0.0 = fails entirely.
Respond ONLY with a JSON object: {{"score": <float 0-1>, "rationale": "<1-2 sentence reason>"}}.
"""
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

def main() -> None:
    # Ensure env vars from project .env are available (including GEMINI_API_KEY)
    load_project_env()
    args = parse_args()
    test_path = args.tests or (args.agent_dir / "evaluation" / "test.json")
    cases = load_cases(test_path)
    if args.max_cases:
        cases = cases[: args.max_cases]

    agent = load_agent(args.agent_dir)
    judge = Judge()

    total_score = 0.0
    table: List[Tuple[str, float, str]] = []

    for idx, case in enumerate(cases, start=1):
        case_input = case["input"]
        # Support both expected_output_type (for regular agents) and expected_redirect (for orchestrator)
        expected = case.get("expected_output_type") or case.get("expected_redirect", "unspecified")
        if isinstance(expected, list):
            expected = f"redirect to agents: {', '.join(expected)}"
        elif expected and expected != "unspecified":
            expected = f"redirect to: {expected}" if "expected_redirect" in case else expected
        description = case.get("description", f"Case #{idx}")

        if args.dry_run:
            print(f"[{idx}/{len(cases)}] {description} -> skipped (dry-run)")
            continue

        agent_output = run_agent_case(agent, case_input)
        result = judge.score(description, expected, case_input, agent_output)
        total_score += result.score
        table.append((description, result.score, result.rationale))
        print(f"[{idx}/{len(cases)}] {description} -> {result.score:.2f} ({result.rationale})")

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
