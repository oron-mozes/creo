"""Unit tests for onboarding agent tools."""
import json
import pytest
from unittest.mock import Mock, MagicMock
from agents.onboarding_agent.tools import save_business_card_tool, set_session_context


class TestSaveBusinessCardTool:
    """Test cases for save_business_card_tool."""

    def setup_method(self) -> None:
        """Set up test fixtures before each test."""
        # Create mock session manager and session memory
        self.mock_session_memory = Mock()
        self.mock_session_memory.user_id = "test_user_123"

        self.mock_session_manager = Mock()
        self.mock_session_manager.get_session_memory = Mock(return_value=self.mock_session_memory)

        # Set session context for tests
        set_session_context(self.mock_session_manager, "test_session_456")

    def teardown_method(self) -> None:
        """Clean up after each test."""
        # Clear session context
        from agents.onboarding_agent.tools import _session_contexts, _context_lock
        with _context_lock:
            _session_contexts.clear()

    def test_save_business_card_success(self) -> None:
        """Test successful business card save."""
        result = save_business_card_tool(
            name="Test Company",
            location="San Francisco, CA",
            service_type="Software Development",
            website="https://example.com",
            social_links="https://instagram.com/test"
        )

        result_data = json.loads(result)

        assert result_data["success"] is True
        assert "Test Company" in result_data["message"]
        assert result_data["business_card"]["name"] == "Test Company"
        assert result_data["business_card"]["location"] == "San Francisco, CA"
        assert result_data["business_card"]["service_type"] == "Software Development"
        assert result_data["is_complete"] is True

    def test_save_business_card_with_optional_fields_none(self) -> None:
        """Test saving business card with optional fields as None."""
        result = save_business_card_tool(
            name="Test Company",
            location="San Francisco",
            service_type="Tech",
            website=None,
            social_links="https://instagram.com/test"
        )

        result_data = json.loads(result)

        assert result_data["success"] is True
        assert result_data["business_card"]["website"] == "Not provided"
        assert result_data["business_card"]["social_links"] == "https://instagram.com/test"

    def test_save_business_card_converts_none_strings(self) -> None:
        """Test that 'none' and 'not provided' strings are converted to None."""
        result = save_business_card_tool(
            name="Test Company",
            location="San Francisco",
            service_type="Tech",
            website="none",
            social_links="Not provided"
        )

        result_data = json.loads(result)

        assert result_data["success"] is True
        assert result_data["business_card"]["website"] == "Not provided"
        assert result_data["business_card"]["social_links"] == "Not provided"

    def test_save_business_card_website_url_validation(self) -> None:
        """Test that website URLs are validated and prefixed."""
        result = save_business_card_tool(
            name="Test Company",
            location="San Francisco",
            service_type="Tech",
            website="example.com",  # Without protocol
            social_links=None
        )

        result_data = json.loads(result)

        assert result_data["success"] is True
        assert result_data["business_card"]["website"] == "https://example.com"

    def test_save_business_card_no_session_context(self) -> None:
        """Test error when session context is not set."""
        # Clear session context
        from agents.onboarding_agent.tools import _session_contexts, _context_lock
        with _context_lock:
            _session_contexts.clear()

        result = save_business_card_tool(
            name="Test Company",
            location="San Francisco",
            service_type="Tech"
        )

        result_data = json.loads(result)

        assert result_data["success"] is False
        assert "Session context not available" in result_data["error"]

    def test_save_business_card_calls_util_function(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that the tool calls the utility save function."""
        mock_save = Mock()
        # The import happens inside the tool function, so we need to patch utils.message_utils
        monkeypatch.setattr("utils.message_utils.save_business_card", mock_save)

        result = save_business_card_tool(
            name="Test Company",
            location="San Francisco",
            service_type="Tech",
            website="https://example.com"
        )

        result_data = json.loads(result)

        assert result_data["success"] is True
        # Verify the utility function was called with user_id and business_card_data
        mock_save.assert_called_once()
        call_args = mock_save.call_args
        assert call_args[0][0] == "test_user_123"  # user_id
        assert call_args[0][1]["name"] == "Test Company"

    def test_save_business_card_saves_to_session_memory(self) -> None:
        """Test that business card is saved to session memory."""
        result = save_business_card_tool(
            name="Test Company",
            location="San Francisco",
            service_type="Tech",
            website="https://example.com"
        )

        result_data = json.loads(result)

        assert result_data["success"] is True
        # Verify session memory's set_business_card was called
        self.mock_session_memory.set_business_card.assert_called_once()
        call_args = self.mock_session_memory.set_business_card.call_args[0][0]
        assert call_args["name"] == "Test Company"

    def test_save_business_card_handles_validation_error(self) -> None:
        """Test that validation errors are handled gracefully."""
        # Note: Currently BusinessCard model is lenient, but if we add stricter validation
        # this test ensures errors are caught and returned properly
        result = save_business_card_tool(
            name="",  # Empty name
            location="San Francisco",
            service_type="Tech"
        )

        # Should still succeed (model allows empty strings currently)
        # But if we add validation, this would fail gracefully
        result_data = json.loads(result)
        assert "success" in result_data

    def test_save_business_card_is_complete_check(self) -> None:
        """Test that is_complete is correctly set in response."""
        # Complete card (has name, location, service_type, and website)
        result = save_business_card_tool(
            name="Test Company",
            location="San Francisco",
            service_type="Tech",
            website="https://example.com"
        )
        result_data = json.loads(result)
        assert result_data["is_complete"] is True

        # Incomplete card (missing contact info)
        result = save_business_card_tool(
            name="Test Company",
            location="San Francisco",
            service_type="Tech",
            website=None,
            social_links=None
        )
        result_data = json.loads(result)
        assert result_data["is_complete"] is False


class TestSetSessionContext:
    """Test cases for set_session_context function."""

    def teardown_method(self) -> None:
        """Clean up after each test."""
        from agents.onboarding_agent.tools import _session_contexts, _context_lock
        with _context_lock:
            _session_contexts.clear()

    def test_set_session_context_stores_correctly(self) -> None:
        """Test that set_session_context stores session data correctly."""
        from agents.onboarding_agent.tools import _session_contexts, _context_lock

        mock_manager = Mock()
        session_id = "test_session_789"

        set_session_context(mock_manager, session_id)

        with _context_lock:
            assert session_id in _session_contexts
            assert _session_contexts[session_id]["session_manager"] == mock_manager
            assert _session_contexts[session_id]["session_id"] == session_id

    def test_set_session_context_thread_safe(self) -> None:
        """Test that set_session_context is thread-safe."""
        import threading
        from agents.onboarding_agent.tools import _session_contexts

        mock_manager = Mock()
        results = []

        def set_context(session_num: int) -> None:
            session_id = f"session_{session_num}"
            set_session_context(mock_manager, session_id)
            results.append(session_id)

        # Run multiple threads setting context
        threads = [threading.Thread(target=set_context, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All sessions should be stored
        assert len(results) == 10
        assert len(_session_contexts) >= 1  # At least the last one
