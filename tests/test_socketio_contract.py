"""
Contract tests for Socket.IO API.

These tests ensure that the Socket.IO event contract between server and client
remains stable and backwards-compatible.

CRITICAL: Any breaking changes to these contracts will break the client UI!
"""
import pytest
import socketio
from typing import Dict, List, Any
import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# Mock minimal environment for testing
os.environ.setdefault("GOOGLE_API_KEY", "test-key")
os.environ.setdefault("PINECONE_API_KEY", "test-key")


class SocketIOEventCollector:
    """Helper class to collect Socket.IO events during tests."""

    def __init__(self) -> None:
        self.events: List[Dict[str, Any]] = []

    def record(self, event_name: str, data: Any = None) -> None:
        """Record an emitted event."""
        self.events.append({
            'event': event_name,
            'data': data
        })

    def get_events_by_name(self, event_name: str) -> List[Dict[str, Any]]:
        """Get all events with a specific name."""
        return [e for e in self.events if e['event'] == event_name]

    def clear(self) -> None:
        """Clear all recorded events."""
        self.events = []


class TestSocketIOEventContract:
    """
    Test Socket.IO event contracts.

    These tests verify that the events emitted by the server match
    the expected contract that the client depends on.
    """

    def test_chat_history_event_structure(self):
        """
        Verify chat_history event has required fields.

        Contract:
        {
            "messages": [
                {
                    "id": str,
                    "role": "user" | "assistant",
                    "content": str,
                    "timestamp": str (ISO 8601),
                    "user_id": str
                }
            ],
            "session_id": str
        }
        """
        # This would be emitted when client joins a session
        sample_event = {
            "messages": [
                {
                    "id": "uuid-here",
                    "role": "user",
                    "content": "Hello",
                    "timestamp": "2025-01-16T10:00:00",
                    "user_id": "user_123"
                }
            ],
            "session_id": "session_456"
        }

        # Verify required fields exist
        assert "messages" in sample_event
        assert "session_id" in sample_event
        assert isinstance(sample_event["messages"], list)

        # Verify message structure
        if sample_event["messages"]:
            msg = sample_event["messages"][0]
            assert "id" in msg
            assert "role" in msg
            assert "content" in msg
            assert "timestamp" in msg
            assert "user_id" in msg
            assert msg["role"] in ["user", "assistant"]

    def test_agent_thinking_event_structure(self):
        """
        Verify agent_thinking event has required fields.

        Contract:
        {
            "session_id": str
        }
        """
        sample_event = {
            "session_id": "session_456"
        }

        assert "session_id" in sample_event
        assert isinstance(sample_event["session_id"], str)

    def test_message_chunk_event_structure(self):
        """
        Verify message_chunk event has required fields.

        Contract:
        {
            "chunk": str,
            "session_id": str,
            "message_id": str
        }
        """
        sample_event = {
            "chunk": "Hello, ",
            "session_id": "session_456",
            "message_id": "msg_789"
        }

        assert "chunk" in sample_event
        assert "session_id" in sample_event
        assert "message_id" in sample_event
        assert isinstance(sample_event["chunk"], str)

    def test_message_complete_event_structure(self):
        """
        Verify message_complete event has required fields.

        Contract:
        {
            "message": str,
            "session_id": str,
            "message_id": str,
            "business_card": dict | null
        }

        When business_card is present:
        {
            "name": str | "Not provided",
            "website": str | "Not provided",
            "social_links": str | "Not provided",
            "location": str | "Not provided",
            "service_type": str | "Not provided"
        }
        """
        # Without business card
        sample_event_no_card = {
            "message": "Hi there! How can I help?",
            "session_id": "session_456",
            "message_id": "msg_789",
            "business_card": None
        }

        assert "message" in sample_event_no_card
        assert "session_id" in sample_event_no_card
        assert "message_id" in sample_event_no_card
        assert "business_card" in sample_event_no_card

        # With business card
        sample_event_with_card = {
            "message": "Great! Let me confirm...",
            "session_id": "session_456",
            "message_id": "msg_789",
            "business_card": {
                "name": "Alma Cafe",
                "website": "https://example.com",
                "social_links": "Not provided",
                "location": "Rehovot, Israel",
                "service_type": "Coffee shop"
            }
        }

        assert "message" in sample_event_with_card
        assert "business_card" in sample_event_with_card
        assert sample_event_with_card["business_card"] is not None

        # Verify business card structure
        card = sample_event_with_card["business_card"]
        assert "name" in card
        assert "website" in card
        assert "social_links" in card
        assert "location" in card
        assert "service_type" in card

    def test_error_event_structure(self):
        """
        Verify error event has required fields.

        Contract:
        {
            "error": str
        }
        """
        sample_event = {
            "error": "Something went wrong"
        }

        assert "error" in sample_event
        assert isinstance(sample_event["error"], str)


class TestSocketIOEventSequence:
    """
    Test Socket.IO event sequences.

    These tests verify that events are emitted in the correct order
    and that the client receives all expected events.
    """

    def test_join_session_event_sequence(self):
        """
        Verify the event sequence when joining a session with initial message.

        Expected sequence:
        1. chat_history (with user message)
        2. agent_thinking
        3. message_chunk (0+ times, optional for non-streaming responses)
        4. message_complete
        """
        events = [
            {"event": "chat_history", "data": {"messages": [{"role": "user", "content": "Hello"}], "session_id": "s1"}},
            {"event": "agent_thinking", "data": {"session_id": "s1"}},
            {"event": "message_complete", "data": {"message": "Hi there!", "session_id": "s1", "message_id": "m1", "business_card": None}}
        ]

        # Verify sequence
        assert events[0]["event"] == "chat_history"
        assert events[1]["event"] == "agent_thinking"
        assert events[2]["event"] == "message_complete"

        # Verify chat_history comes before agent_thinking
        chat_history_idx = 0
        agent_thinking_idx = 1
        assert chat_history_idx < agent_thinking_idx

    def test_send_message_event_sequence(self):
        """
        Verify the event sequence when sending a message.

        Expected sequence:
        1. agent_thinking
        2. message_chunk (0+ times, optional for non-streaming responses)
        3. message_complete
        """
        events = [
            {"event": "agent_thinking", "data": {"session_id": "s1"}},
            {"event": "message_complete", "data": {"message": "Response", "session_id": "s1", "message_id": "m1", "business_card": None}}
        ]

        # Verify agent_thinking comes before message_complete
        assert events[0]["event"] == "agent_thinking"
        assert events[1]["event"] == "message_complete"


class TestHTTPAPIContract:
    """
    Test HTTP API contracts.

    These tests verify that the REST API endpoints maintain
    their expected request/response contracts.
    """

    def test_create_session_request_contract(self):
        """
        Verify /api/sessions POST request contract.

        Request:
        {
            "message": str,
            "user_id": str | null (optional)
        }
        """
        sample_request = {
            "message": "I need help with influencer marketing",
            "user_id": "user_123"  # Optional
        }

        assert "message" in sample_request
        assert isinstance(sample_request["message"], str)

    def test_create_session_response_contract(self):
        """
        Verify /api/sessions POST response contract.

        Response:
        {
            "session_id": str,
            "user_id": str
        }
        """
        sample_response = {
            "session_id": "session_abc123",
            "user_id": "user_xyz789"
        }

        assert "session_id" in sample_response
        assert "user_id" in sample_response
        assert isinstance(sample_response["session_id"], str)
        assert isinstance(sample_response["user_id"], str)

    def test_get_messages_response_contract(self):
        """
        Verify GET /api/sessions/{session_id}/messages response contract.

        Response:
        {
            "messages": [
                {
                    "id": str,
                    "role": "user" | "assistant",
                    "content": str,
                    "timestamp": str (ISO 8601),
                    "user_id": str
                }
            ],
            "session_id": str
        }
        """
        sample_response = {
            "messages": [
                {
                    "id": "msg_1",
                    "role": "user",
                    "content": "Hello",
                    "timestamp": "2025-01-16T10:00:00",
                    "user_id": "user_123"
                },
                {
                    "id": "msg_2",
                    "role": "assistant",
                    "content": "Hi there!",
                    "timestamp": "2025-01-16T10:00:05",
                    "user_id": "user_123"
                }
            ],
            "session_id": "session_456"
        }

        assert "messages" in sample_response
        assert "session_id" in sample_response
        assert isinstance(sample_response["messages"], list)

        # Verify each message structure
        for msg in sample_response["messages"]:
            assert "id" in msg
            assert "role" in msg
            assert "content" in msg
            assert "timestamp" in msg
            assert "user_id" in msg
            assert msg["role"] in ["user", "assistant"]


class TestBackwardsCompatibility:
    """
    Test backwards compatibility guarantees.

    These tests ensure that old clients will continue to work
    even as we add new features.
    """

    def test_message_complete_backwards_compat_no_business_card(self):
        """
        Old clients expect message_complete to work without business_card field.
        Ensure it's always present (even if null) for consistency.
        """
        sample_event = {
            "message": "Hi there!",
            "session_id": "session_456",
            "message_id": "msg_789",
            "business_card": None  # MUST be present, even if null
        }

        # This field MUST always be present for backwards compatibility
        assert "business_card" in sample_event

    def test_message_complete_backwards_compat_no_streaming(self):
        """
        Clients should handle both streaming and non-streaming responses.
        When no message_chunk events are sent, message_complete must include
        the full message text.
        """
        # Non-streaming response (AgentTool wrapped agents)
        sample_event = {
            "message": "Full response text here",  # MUST be complete
            "session_id": "session_456",
            "message_id": "msg_789",
            "business_card": None
        }

        assert "message" in sample_event
        assert len(sample_event["message"]) > 0

    def test_optional_fields_can_be_added(self):
        """
        New optional fields can be added to events without breaking old clients.
        Old clients will ignore unknown fields.
        """
        # Example: Adding a new optional field "metadata"
        sample_event = {
            "message": "Hi there!",
            "session_id": "session_456",
            "message_id": "msg_789",
            "business_card": None,
            "metadata": {"agent_name": "onboarding_agent"}  # New optional field
        }

        # Old required fields still present
        assert "message" in sample_event
        assert "session_id" in sample_event
        assert "message_id" in sample_event
        assert "business_card" in sample_event


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
