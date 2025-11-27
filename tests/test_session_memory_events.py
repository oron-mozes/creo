from session_manager import SessionMemory
from workflow_enums import MessageRole


def test_add_agent_event_stores_content():
    mem = SessionMemory(user_id="u1", session_id="s1")
    mem.add_agent_event("agent_a", "hello", is_final=False)
    mem.add_agent_event("agent_b", "done", is_final=True)

    events = mem.get_shared_context().get("agent_events", [])
    assert len(events) == 2
    assert events[0]["agent"] == "agent_a"
    assert events[0]["content"] == "hello"
    assert events[0]["is_final"] is False
    assert events[1]["agent"] == "agent_b"
    assert events[1]["is_final"] is True


def test_add_agent_event_skips_empty():
    mem = SessionMemory(user_id="u1", session_id="s1")
    mem.add_agent_event("agent_a", "", is_final=False)
    events = mem.get_shared_context().get("agent_events", [])
    assert events == []


def test_add_message_uses_roles():
    mem = SessionMemory(user_id="u1", session_id="s1")
    mem.add_message(MessageRole.USER.value, "hi")
    assert mem.get_shared_context()["messages"][0]["role"] == MessageRole.USER.value
