# Agent Evaluation Guide

This guide explains how to evaluate and test agents in the Creo system.

---

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Test Generation](#test-generation)
4. [Running Evaluations](#running-evaluations)
5. [Understanding Results](#understanding-results)
6. [Writing Good Examples](#writing-good-examples)
7. [Best Practices](#best-practices)
8. [Troubleshooting](#troubleshooting)

---

## Overview

The evaluation system uses:
- **Golden tests** - Hardcoded critical test cases in `agents/test_utils.py`
- **LLM-generated tests** - Automatically generated from `instruction.md` + `examples.md`
- **Hybrid approach** - Combines both for comprehensive coverage
- **LLM judge** - Evaluates agent responses against expected behavior

---

## Quick Start

### Evaluate an Agent

```bash
# 1. Generate test cases (hybrid: golden + LLM)
make generate-tests AGENT=onboarding-agent

# 2. Run evaluation
make judge AGENT=onboarding-agent
```

That's it! The evaluation report will be saved to `agents/onboarding-agent/evaluation/report.json`.

---

## Test Generation

### Command Options

```bash
# Generate tests for a specific agent (RECOMMENDED)
make generate-tests AGENT=onboarding-agent

# Generate tests for ALL agents
make generate-tests
```

### How It Works

The `make generate-tests` command uses the **hybrid approach**:

1. **Loads golden tests** from `agents/test_utils.py`
   - These are manually curated critical test cases
   - Guaranteed to cover important user journeys
   - Example: 6-15 tests per agent

2. **Generates LLM tests** from agent's documentation
   - Reads `agents/<agent-name>/instruction.md`
   - Reads `agents/<agent-name>/examples.md`
   - Uses Gemini 2.0 to generate diverse test cases
   - Example: 10 additional tests

3. **Merges and deduplicates**
   - Combines golden + LLM tests
   - Removes duplicates by test name
   - Result: 15-25 comprehensive test cases

### Test File Location

Generated tests are saved to:
```
agents/<agent-name>/evaluation/test.json
```

---

## Running Evaluations

### Evaluate a Single Agent

```bash
make judge AGENT=onboarding-agent
```

**Output:**
- Shows progress for each test case
- Displays score (0.0 to 1.0) and rationale
- Saves full report to `agents/<agent-name>/evaluation/report.json`

### Evaluate All Agents

```bash
# Generate tests for all
make generate-tests

# Run evaluations (repeat for each agent)
make judge AGENT=onboarding-agent
make judge AGENT=orchestrator-agent
make judge AGENT=frontdesk-agent
# etc.
```

---

## Understanding Results

### Report Structure

The `report.json` file contains:

```json
{
  "average_confidence_score": 0.98,
  "total_cases": 25,
  "test_results": [
    {
      "description": "User provides website URL...",
      "score": 1.0,
      "rationale": "The agent correctly..."
    }
  ]
}
```

### Score Interpretation

| Score | Meaning | Action |
|-------|---------|--------|
| **1.0** | Perfect | ✅ Test passed |
| **0.7-0.9** | Good with minor issues | ⚠️ Review rationale |
| **0.4-0.6** | Partial | 🔍 Needs improvement |
| **0.0-0.3** | Failed | ❌ Critical issue |

### Average Confidence Score

- **0.9+** - Excellent performance
- **0.7-0.9** - Good, minor improvements needed
- **0.5-0.7** - Moderate, review failures
- **<0.5** - Poor, major issues

---

## Writing Good Examples

The quality of LLM-generated tests depends on your `examples.md` file.

### Structure of examples.md

```markdown
# AGENT NAME EXAMPLES

These examples align 1:1 with test cases.

---

## Example 1: Clear scenario name

**User message:** "Exact user input"

**Context:** business_card=null

**Agent response:**
```
[Show the exact expected response format]

BUSINESS_CARD_CONFIRMATION:
{
  "name": "Example Corp",
  ...
}
```

**Note:** Explain key behaviors or edge cases
```

### Best Practices for Examples

1. **Be Specific**
   - Show EXACT user input
   - Show EXACT expected output format
   - Include all required data blocks

2. **Cover Edge Cases**
   - Vague inputs
   - Corrections/clarifications
   - Error handling
   - Boundary conditions

3. **Show Context**
   - Indicate session state (`business_card`, `workflow_state`)
   - Show conversation history if relevant

4. **Add Variety**
   - Different input formats (URL, name+location, social handles)
   - Different user behaviors (confirms, corrects, clarifies)
   - Different scenarios (new user, returning user, etc.)

### Example Template

```markdown
## Example X: [Scenario Name]

**User message:** "[Exact user input]"

**Context:** business_card=null, workflow_state={}

**Agent response:**
```
[Expected agent response showing:
- User-friendly message
- Any required data blocks
- Proper formatting]
```

**Note:** [Why this is important / what it tests]

---
```

---

## Best Practices

### 1. Iterate on Examples

```bash
# 1. Update examples.md with new edge cases
vim agents/onboarding-agent/examples.md

# 2. Regenerate tests
make generate-tests AGENT=onboarding-agent

# 3. Run evaluation
make judge AGENT=onboarding-agent

# 4. Review failures, update examples, repeat
```

### 2. Maintain Golden Tests

Edit `agents/test_utils.py` to add critical test cases that should ALWAYS be tested:

```python
def generate_onboarding_agent_tests() -> List[Dict[str, Any]]:
    return [
        {
            "name": "critical_user_flow",
            "description": "Test the most important user journey",
            "user_message": "...",
            "session_context": {...},
            "expected_behavior": {...}
        },
        # Add more golden tests
    ]
```

### 3. Review Failures Systematically

When tests fail:

1. **Read the rationale** - Judge explains WHY it failed
2. **Check the instructions** - Is guidance clear in `instruction.md`?
3. **Update examples** - Add example showing correct behavior
4. **Regenerate & retest** - Verify the fix

### 4. Track Progress

```bash
# Before improvements
make judge AGENT=onboarding-agent
# Note the average_confidence_score

# After improvements
make generate-tests AGENT=onboarding-agent
make judge AGENT=onboarding-agent
# Compare scores
```

---

## Troubleshooting

### "No test cases generated"

**Problem:** LLM failed to generate tests

**Solutions:**
1. Check that `instruction.md` and `examples.md` exist
2. Verify `GOOGLE_API_KEY` is set in `.env`
3. Check LLM output for JSON parsing errors
4. Try regenerating: `make generate-tests AGENT=<agent-name>`

### "All tests scoring 0.0"

**Problem:** Agent not following instructions

**Solutions:**
1. Review `instruction.md` - is it clear and unambiguous?
2. Check for contradictions between instruction and examples
3. Add more concrete examples to `examples.md`
4. Verify agent has access to required tools

### "LLM judge giving inconsistent scores"

**Problem:** Non-deterministic evaluation

**Solutions:**
1. Make expected behaviors more specific in test cases
2. Add `expected_response_contains` keywords to test cases
3. Update examples to show exact output format
4. Run evaluation multiple times to check consistency

### "Tests pass but agent fails in production"

**Problem:** Tests don't cover real-world scenarios

**Solutions:**
1. Add production failure cases to `examples.md`
2. Create golden tests for critical user flows
3. Increase diversity by generating more LLM tests
4. Review user feedback and add those scenarios

---

## Advanced Usage

### Custom Test Generation

For fine-grained control, use the Python script directly:

```bash
# LLM-only tests (15 tests)
venv/bin/python3 scripts/generate_tests_with_llm.py onboarding-agent

# Hybrid tests (golden + LLM)
venv/bin/python3 scripts/generate_tests_with_llm.py --hybrid onboarding-agent
```

### Batch Evaluation

Evaluate all agents and collect results:

```bash
#!/bin/bash
for agent in onboarding-agent orchestrator-agent frontdesk-agent; do
  echo "Evaluating $agent..."
  make judge AGENT=$agent
  score=$(cat agents/$agent/evaluation/report.json | jq '.average_confidence_score')
  echo "$agent: $score"
done
```

---

## Test Case Format Reference

```json
{
  "name": "unique_test_name",
  "description": "What this test validates",
  "user_message": "The exact user input",
  "session_context": {
    "business_card": null,
    "workflow_state": {},
    "last_agent_message": ""
  },
  "expected_behavior": {
    "should_use_google_search": true,
    "should_generate_confirmation_block": true,
    "should_ask_for_confirmation": true
  },
  "expected_response_contains": ["keyword1", "keyword2"],
  "expected_business_card": {
    "name": "Business Name",
    "location": "City, State"
  }
}
```

---

## Summary: Evaluation Workflow

```
┌─────────────────────────────────────────┐
│ 1. Write clear instruction.md          │
│ 2. Add diverse examples to examples.md │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│ 3. Generate tests (hybrid)              │
│    make generate-tests AGENT=<name>    │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│ 4. Run evaluation                       │
│    make judge AGENT=<name>             │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│ 5. Review report.json                   │
│    - Check average_confidence_score     │
│    - Read failure rationales            │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│ 6. Fix issues                           │
│    - Update instruction.md              │
│    - Add examples for failures          │
│    - Update golden tests if needed      │
└────────────────┬────────────────────────┘
                 │
                 ▼
               Repeat
```

---

## Questions?

- Check `docs/CONTRIBUTING.md` for code guidelines
- See `agents/<agent-name>/instruction.md` for agent behavior
- Review `agents/<agent-name>/examples.md` for expected patterns
- Examine `agents/test_utils.py` for golden test definitions
