import importlib
import types

import pytest


def _reset_in_memory(message_utils):
    message_utils.in_memory_campaign_briefs.clear()
    message_utils.in_memory_messages.clear()
    message_utils.in_memory_business_cards.clear()
    import db
    db._in_memory_creators.clear()


@pytest.fixture(autouse=True)
def patch_get_db(monkeypatch):
    """Force message_utils to use in-memory storage."""
    import utils.message_utils as message_utils

    monkeypatch.setattr(message_utils, "get_db", lambda: None)
    _reset_in_memory(message_utils)
    yield
    _reset_in_memory(message_utils)


def test_save_campaign_brief_in_memory(monkeypatch):
    import utils.message_utils as message_utils

    brief = {"goal": "Test", "platform": "YouTube"}
    session_id = "session123"
    user_id = "user123"

    message_utils.save_campaign_brief(user_id, session_id, brief)

    assert session_id in message_utils.in_memory_campaign_briefs
    assert message_utils.in_memory_campaign_briefs[session_id] == brief


def test_get_campaign_brief_in_memory(monkeypatch):
    import utils.message_utils as message_utils

    brief = {"goal": "Another Test", "platform": "TikTok"}
    session_id = "session456"
    message_utils.in_memory_campaign_briefs[session_id] = brief

    result = message_utils.get_campaign_brief(session_id)
    assert result == brief


def test_get_campaign_brief_missing(monkeypatch):
    import utils.message_utils as message_utils

    session_id = "missing_session"
    result = message_utils.get_campaign_brief(session_id)
    assert result is None


def test_save_creators_for_session_in_memory(monkeypatch):
    import utils.message_utils as message_utils
    import db

    creators = [{"name": "Alice"}, {"name": "Bob"}]
    session_id = "sess-creators"
    user_id = "user-creators"

    message_utils.save_creators_for_session(creators, session_id, user_id)

    stored = [c for c in db._in_memory_creators if c.get("session_id") == session_id]
    assert len(stored) == 2
    assert stored[0]["user_id"] == user_id
    assert stored[0]["status"] == "pending"


def test_get_creators_for_session_in_memory(monkeypatch):
    import utils.message_utils as message_utils
    import db

    db._in_memory_creators.clear()
    db._in_memory_creators.append({"name": "Alice", "session_id": "sess1"})
    db._in_memory_creators.append({"name": "Bob", "session_id": "sess2"})

    results = message_utils.get_creators_for_session("sess1")
    assert len(results) == 1
    assert results[0]["name"] == "Alice"
