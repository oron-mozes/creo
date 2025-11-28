import asyncio
from types import SimpleNamespace

import pytest


class DummyRunner:
    def __init__(self, app_name=None, agent=None):
        self.app_name = app_name
        self.agent = agent


class DummyEvent:
    def __init__(self, text=None):
        self.parts = []
        if text is not None:
            class Part:
                def __init__(self, t):
                    self.text = t
            self.parts = [Part(text)]


class DummyAgent:
    name = "dummy_agent"

    async def run_async(self, request, *args, **kwargs):
        # Simulate returning a list (not an async iterator): string + event
        return ["bad_string", DummyEvent(text="ok")]


@pytest.mark.asyncio
async def test_run_agent_with_dummy_runner(monkeypatch):
    import agents.orchestrator_agent.tools as tools

    dummy_agent = DummyAgent()

    # Patch InMemoryRunner to avoid constructor signature errors
    monkeypatch.setattr(tools, "InMemoryRunner", DummyRunner)

    tc = SimpleNamespace(session=SimpleNamespace(session_id="s", user_id="u", app_name="app"), runner=None)

    result = await tools._run_agent_and_get_text(dummy_agent, tc, "hello")
    # Should capture only valid event parts and ignore bad payloads
    assert result == "ok"


def test_set_workflow_stage_tool_json_errors(monkeypatch):
    import agents.orchestrator_agent.tools as tools

    tc = SimpleNamespace(session=None)
    res = asyncio.get_event_loop().run_until_complete(tools._set_workflow_stage_fn("invalid", tc))
    assert res.get("success") is False
    assert "error" in res


def test_missing_session_is_error(monkeypatch):
    import agents.orchestrator_agent.tools as tools
    dummy_agent = DummyAgent()
    tc = SimpleNamespace(session=None, runner=None)
    with pytest.raises(ValueError):
        asyncio.get_event_loop().run_until_complete(tools._run_agent_and_get_text(dummy_agent, tc, "hello"))


@pytest.mark.asyncio
async def test_run_agent_with_id_session(monkeypatch):
    import agents.orchestrator_agent.tools as tools

    dummy_agent = DummyAgent()
    monkeypatch.setattr(tools, "InMemoryRunner", DummyRunner)

    # Session provides id instead of session_id
    tc = SimpleNamespace(session=SimpleNamespace(id="s2", user_id="u2", app_name="app"), runner=None)
    result = await tools._run_agent_and_get_text(dummy_agent, tc, "hello")
    assert result == "ok"
