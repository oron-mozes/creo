import types
import uuid

import pytest

from sockets.handlers import run_agent as ra
from workflow_enums import MessageRole


class FakeSio:
    def __init__(self):
        self.calls = []
        self.emitted = []

    def start_background_task(self, func, *args, **kwargs):
        # Execute immediately for testing; run coroutines to completion
        import asyncio
        self.calls.append((func, args, kwargs))
        res = func(*args, **kwargs)
        if asyncio.iscoroutine(res):
            asyncio.get_event_loop().run_until_complete(res)
        return res

    async def emit(self, event, payload, room=None):
        self.emitted.append((event, payload, room))


class FakeSessionMemory:
    def __init__(self, stage=None, brief=False, business_card=None):
        self.stage = stage
        self.agent_ctx = {"campaign_brief_agent": {"brief": "x"}} if brief else {}
        self.bc = business_card
        self.agent_events = []

    def get_workflow_stage(self):
        return self.stage

    def get_agent_context(self, name):
        return self.agent_ctx.get(name, {})

    def get_business_card(self):
        return self.bc

    def add_agent_event(self, agent, content, is_final=False):
        self.agent_events.append((agent, content, is_final))


class FakeSessionManager:
    def __init__(self, memory=None):
        self.memory = memory

    def get_session_memory(self, session_id):
        return self.memory

    def save_assistant_message(self, session_id, content, message_id=None):
        # no-op for tests
        pass

    def run_agent(self, **kwargs):
        # Not used in unit tests of helpers
        yield from ()


class FakeMessageStore:
    def __init__(self):
        self.saved = []

    def save_message(self, session_id, role, message, user_id):
        self.saved.append((session_id, role, message, user_id))


def test_handle_frontdesk_chunk_streams_and_records():
    sio = FakeSio()
    resp_chunks = []
    ra._handle_frontdesk_chunk("hi", ra.AgentName.FRONTDESK_AGENT.value, sio, "s1", "m1", resp_chunks)
    assert resp_chunks == ["hi"]
    assert sio.emitted[0][0] == ra.SocketEvent.MESSAGE_CHUNK.value
    assert sio.emitted[0][1]["chunk"] == "hi"


def test_handle_frontdesk_chunk_ignores_non_frontdesk():
    sio = FakeSio()
    resp_chunks = []
    ra._handle_frontdesk_chunk("hi", "other", sio, "s1", "m1", resp_chunks)
    assert resp_chunks == []
    assert sio.emitted == []


def test_handle_root_final_prompts_login(monkeypatch):
    sio = FakeSio()
    ms = FakeMessageStore()
    sm = FakeSessionManager(memory=None)

    monkeypatch.setattr(ra, "should_prompt_login", lambda stage, has_brief, is_auth: True)

    handled = ra._handle_root_final(
        author="root",
        is_final_event=True,
        final_text="done",
        session_manager=sm,
        session_id="s1",
        user_id="u1",
        is_authenticated=False,
        message_store=ms,
        message_id="mid",
        sio=sio,
        root_agent=types.SimpleNamespace(name="root"),
    )
    assert handled is True
    assert any(call[1][0] == ra.SocketEvent.MESSAGE_COMPLETE.value for call in sio.calls)
    assert ms.saved[0][1] == MessageRole.ASSISTANT.value


def test_handle_root_final_saves_final(monkeypatch):
    sio = FakeSio()
    ms = FakeMessageStore()
    mem = FakeSessionMemory(stage=None, brief=False, business_card={"x": 1})
    sm = FakeSessionManager(memory=mem)
    monkeypatch.setattr(ra, "should_prompt_login", lambda stage, has_brief, is_auth: False)

    handled = ra._handle_root_final(
        author="root",
        is_final_event=True,
        final_text="done",
        session_manager=sm,
        session_id="s1",
        user_id="u1",
        is_authenticated=False,
        message_store=ms,
        message_id="mid",
        sio=sio,
        root_agent=types.SimpleNamespace(name="root"),
    )
    assert handled is True
    assert ms.saved[0][2] == "done"
    assert sio.calls[0][1][1]["message"] == "done"


@pytest.mark.asyncio
async def test_emit_fallback_prefers_frontdesk():
    sio = FakeSio()
    ms = FakeMessageStore()
    sm = FakeSessionManager()
    await ra._emit_fallback_response(
        sio=sio,
        session_id="s1",
        message_id="mid",
        message_store=ms,
        session_manager=sm,
        user_id="u1",
        response_chunks=["a", "b"],
        all_chunks=[],
    )
    assert ms.saved[0][2] == "ab"
    assert sio.emitted[-1][0] == ra.SocketEvent.MESSAGE_COMPLETE.value


@pytest.mark.asyncio
async def test_emit_fallback_uses_all_chunks():
    sio = FakeSio()
    ms = FakeMessageStore()
    sm = FakeSessionManager()
    await ra._emit_fallback_response(
        sio=sio,
        session_id="s1",
        message_id="mid",
        message_store=ms,
        session_manager=sm,
        user_id="u1",
        response_chunks=[],
        all_chunks=[("a", "x"), ("b", "y")],
    )
    # Should emit a chunk then complete
    assert any(event == ra.SocketEvent.MESSAGE_CHUNK.value for event, _, _ in sio.emitted)
    assert sio.emitted[-1][0] == ra.SocketEvent.MESSAGE_COMPLETE.value
