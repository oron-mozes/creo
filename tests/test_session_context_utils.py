import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import importlib

ctx = importlib.import_module("agents.session_context")


def test_set_and_get_context():
    ctx.set_context("agent_a", session_manager="sm", session_id="s1", user_id="u1")
    c = ctx.get_context("agent_a")
    assert c["session_id"] == "s1"
    assert c["user_id"] == "u1"
    assert c["session_manager"] == "sm"


def test_get_context_with_explicit_session():
    ctx.set_context("agent_b", session_manager="sm2", session_id="s2", user_id="u2")
    c = ctx.get_context("agent_b", session_id="s2")
    assert c["session_id"] == "s2"
    assert c["user_id"] == "u2"


def test_clear_context():
    ctx.set_context("agent_c", session_manager="sm3", session_id="s3", user_id="u3")
    ctx.clear_context("agent_c")
    assert ctx.get_context("agent_c") is None


def test_shared_context_key():
    ctx.set_context("shared", session_manager="sm_shared", session_id="s_shared", user_id="u_shared")
    c = ctx.get_context("shared")
    assert c["session_id"] == "s_shared"
    assert c["user_id"] == "u_shared"
