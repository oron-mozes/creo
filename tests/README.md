# Creo Test Suite

## Overview

This directory contains tests to ensure the stability and correctness of the Creo API.

## Test Categories

### 1. Contract Tests (`test_socketio_contract.py`)

**Purpose**: Ensure the Socket.IO and HTTP API contracts remain stable and backwards-compatible.

**Why it matters**: Breaking changes to the API contract will break the client UI. These tests act as a safety net to catch breaking changes before they reach production.

**What they test**:
- Event structure (required fields, data types)
- Event sequences (order of events)
- Backwards compatibility (adding new fields, maintaining old fields)

**When to update**:
- ✅ When adding new **optional** fields to events
- ✅ When adding new events
- ❌ When removing or renaming fields (breaking change - requires discussion)
- ❌ When changing event sequences (breaking change - requires discussion)

### 2. Integration Tests (TODO)

**Purpose**: Test end-to-end flows with real agents.

**What they test**:
- Full conversation flows
- Agent orchestration
- Business card collection
- Session management

### 3. Unit Tests (TODO)

**Purpose**: Test individual components in isolation.

**What they test**:
- Business card parser
- Session manager
- Individual agent logic

## Running Tests

### Run all tests
```bash
make test
```

### Run contract tests only
```bash
pytest tests/test_socketio_contract.py -v
```

### Run with coverage
```bash
pytest tests/ --cov=. --cov-report=html
```

## Contract Testing Philosophy

### The Contract is a Promise

The API contract is a **promise** we make to our clients (the web UI, mobile apps, etc.). Breaking this promise breaks their applications.

### What is a Breaking Change?

**Breaking changes** require client updates and coordination:
- ❌ Removing required fields
- ❌ Renaming fields or events
- ❌ Changing field types
- ❌ Changing event sequences
- ❌ Removing events

**Non-breaking changes** (safe):
- ✅ Adding new optional fields
- ✅ Adding new events
- ✅ Emitting more events (e.g., more `message_chunk` events)

### When Contract Tests Fail

If contract tests fail, it means you've introduced a **breaking change**. Before proceeding:

1. **Discuss with team** - Is this change necessary?
2. **Update documentation** - Modify `docs/API_CONTRACT.md`
3. **Plan client updates** - How will clients handle this change?
4. **Consider versioning** - Should we version the API?
5. **Update tests** - Add tests for the new contract

### Example: Safe vs Breaking Changes

#### ✅ Safe Change (Adding Optional Field)

```python
# Before
{
  "message": "Hello",
  "session_id": "s1",
  "message_id": "m1",
  "business_card": null
}

# After (safe - old clients will ignore new field)
{
  "message": "Hello",
  "session_id": "s1",
  "message_id": "m1",
  "business_card": null,
  "metadata": {"agent": "onboarding"}  # New optional field
}
```

#### ❌ Breaking Change (Removing Required Field)

```python
# Before
{
  "message": "Hello",
  "session_id": "s1",
  "message_id": "m1",
  "business_card": null
}

# After (BREAKS old clients - they expect business_card field)
{
  "message": "Hello",
  "session_id": "s1",
  "message_id": "m1"
  # business_card field removed - BREAKING!
}
```

## Writing Contract Tests

### Template for New Event Tests

```python
def test_my_new_event_structure(self):
    """
    Verify my_new_event has required fields.

    Contract:
    {
        "field1": str,
        "field2": int
    }
    """
    sample_event = {
        "field1": "value",
        "field2": 123
    }

    # Verify required fields exist
    assert "field1" in sample_event
    assert "field2" in sample_event

    # Verify types
    assert isinstance(sample_event["field1"], str)
    assert isinstance(sample_event["field2"], int)
```

### Template for Event Sequence Tests

```python
def test_my_event_sequence(self):
    """
    Verify events are emitted in correct order.

    Expected sequence:
    1. event_a
    2. event_b
    3. event_c
    """
    events = [
        {"event": "event_a", "data": {}},
        {"event": "event_b", "data": {}},
        {"event": "event_c", "data": {}}
    ]

    # Verify sequence
    assert events[0]["event"] == "event_a"
    assert events[1]["event"] == "event_b"
    assert events[2]["event"] == "event_c"
```

## Continuous Integration

Contract tests run automatically on every pull request via GitHub Actions (`.github/workflows/contract-tests.yml`).

**If tests fail on a PR**:
1. Check the workflow logs for details
2. Review your changes against `docs/API_CONTRACT.md`
3. Update tests if you intentionally changed the contract
4. Coordinate with frontend team if breaking changes are necessary

## Questions?

- **What's the difference between contract tests and integration tests?**
  - Contract tests verify the **shape** of the API (structure, fields, types)
  - Integration tests verify the **behavior** of the API (correctness, business logic)

- **Why do we need contract tests if we have integration tests?**
  - Contract tests are **faster** (no real agent calls)
  - Contract tests catch **structural** changes that might not affect behavior
  - Contract tests serve as **documentation** of the API contract

- **Can I skip contract tests for a quick fix?**
  - No! Contract tests are our safety net. Skipping them can break production clients.

## Contributing

When adding new API features:

1. Write contract tests first (TDD approach)
2. Document the contract in `docs/API_CONTRACT.md`
3. Implement the feature
4. Verify tests pass
5. Get team review before merging

---

**Remember**: The contract is a promise. Don't break promises! 🤝
