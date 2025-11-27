"""Tests for outreach auth gating tools and handlers."""
import sys
from pathlib import Path

import pytest

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from handlers.tool_handlers import handle_tool_calls  # noqa: E402
from agents.outreach_message_agent.tools_auth_handler import handle_require_auth_for_outreach  # noqa: E402


def test_require_auth_handler_returns_marker():
    result = handle_require_auth_for_outreach()
    assert result["auth_required"] is True
    assert result["success"] is False
    assert "Authentication required" in result["error"]


@pytest.mark.parametrize(
    "response_text,expected_detected",
    [
        ("call require_auth_for_outreach before sending email", True),
        ("no tools here", False),
    ],
)
def test_handle_tool_calls_detects_auth_tool(response_text, expected_detected):
    outcome = handle_tool_calls(
        response_text=response_text,
        session_id="session_test",
        user_id="user_test",
        session_manager=None,
    )
    assert outcome["tool_detected"] is expected_detected
    if expected_detected:
        assert outcome["auth_required"] is True
        assert outcome["success"] is False
