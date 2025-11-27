import os
import sys
import importlib

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from agents.session_context import set_context, clear_context  # noqa: E402
from agents.outreach_message_agent import tools_auth  # noqa: E402
from sockets.utils.auth import is_authenticated_user, ANON_PREFIX  # noqa: E402


def test_require_auth_when_not_authenticated():
    clear_context()
    res = tools_auth.require_auth_for_outreach_tool()
    assert res["auth_required"] is True
    assert res["success"] is False


def test_require_auth_when_authenticated():
    clear_context()
    set_context("shared", session_manager=None, session_id="s1", user_id="user123")
    res = tools_auth.require_auth_for_outreach_tool()
    assert res["auth_required"] is False
    assert res["success"] is True


def test_is_authenticated_user_helper():
    assert is_authenticated_user("user123") is True
    assert is_authenticated_user(f"{ANON_PREFIX}abc") is False
    assert is_authenticated_user(None) is False
