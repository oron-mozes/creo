"""Unit tests for business card parser."""
import pytest
from agents.onboarding_agent.parser import extract_business_card_from_response
from agents.onboarding_agent.models import BusinessCard


class TestBusinessCardParser:
    """Test cases for business card parser."""

    def test_extract_business_card_with_valid_confirmation(self):
        """Test extracting business card from valid BUSINESS_CARD_CONFIRMATION block."""
        response = """
Great! I've confirmed your business details.

BUSINESS_CARD_CONFIRMATION:
{
  "name": "Alma Cafe",
  "website": "https://www.almacafe.co.il",
  "social_links": "Not provided",
  "location": "Rehovot, Israel",
  "service_type": "Coffee shop"
}

Let's proceed with your campaign!
"""
        result = extract_business_card_from_response(response)

        assert result["has_confirmation"] is True
        assert result["business_card"] is not None
        assert result["business_card"].name == "Alma Cafe"
        assert result["business_card"].website == "https://www.almacafe.co.il"
        assert result["business_card"].location == "Rehovot, Israel"
        assert result["business_card"].service_type == "Coffee shop"
        assert "Let's proceed with your campaign!" in result["cleaned_text"]

    def test_extract_business_card_no_confirmation(self):
        """Test parsing response without BUSINESS_CARD_CONFIRMATION block."""
        response = "What's your business name?"

        result = extract_business_card_from_response(response)

        assert result["has_confirmation"] is False
        assert result["business_card"] is None
        assert result["cleaned_text"] == "What's your business name?"

    def test_extract_business_card_removes_confirmation_block(self):
        """Test that BUSINESS_CARD_CONFIRMATION block is removed from cleaned text."""
        response = """
Perfect! Here are your details:

BUSINESS_CARD_CONFIRMATION:
{
  "name": "Test Co",
  "website": "test.com",
  "social_links": "None",
  "location": "SF",
  "service_type": "Tech"
}

Next steps...
"""
        result = extract_business_card_from_response(response)

        assert result["has_confirmation"] is True
        assert "BUSINESS_CARD_CONFIRMATION" not in result["cleaned_text"]
        assert "Perfect! Here are your details:" in result["cleaned_text"]
        assert "Next steps..." in result["cleaned_text"]

    def test_extract_business_card_with_none_values(self):
        """Test parsing business card with None/null values."""
        response = """
BUSINESS_CARD_CONFIRMATION:
{
  "name": "Test Co",
  "website": null,
  "social_links": "https://instagram.com/test",
  "location": "San Francisco",
  "service_type": "Tech"
}
"""
        result = extract_business_card_from_response(response)

        assert result["has_confirmation"] is True
        assert result["business_card"].website is None
        assert result["business_card"].social_links == "https://instagram.com/test"

    def test_extract_business_card_invalid_json(self):
        """Test parsing response with invalid JSON in confirmation block."""
        response = """
BUSINESS_CARD_CONFIRMATION:
{
  "name": "Test Co"
  invalid json here
}
"""
        result = extract_business_card_from_response(response)

        # Should handle gracefully - either no confirmation or partial data
        assert result["has_confirmation"] is False or result["business_card"] is None

    def test_extract_business_card_multiple_blocks(self):
        """Test that only the first BUSINESS_CARD_CONFIRMATION block is extracted."""
        response = """
BUSINESS_CARD_CONFIRMATION:
{
  "name": "First Co",
  "website": "first.com",
  "social_links": "None",
  "location": "SF",
  "service_type": "Tech"
}

Some text here.

BUSINESS_CARD_CONFIRMATION:
{
  "name": "Second Co",
  "website": "second.com",
  "social_links": "None",
  "location": "NY",
  "service_type": "Finance"
}
"""
        result = extract_business_card_from_response(response)

        assert result["has_confirmation"] is True
        # Should extract the first one
        assert result["business_card"].name == "First Co"

    def test_extract_business_card_empty_response(self):
        """Test parsing empty response."""
        result = extract_business_card_from_response("")

        assert result["has_confirmation"] is False
        assert result["business_card"] is None
        assert result["cleaned_text"] == ""

    def test_extract_business_card_with_markdown_code_block(self):
        """Test parsing confirmation block inside markdown code block."""
        response = """
Here's your business card:

```
BUSINESS_CARD_CONFIRMATION:
{
  "name": "Test Co",
  "website": "test.com",
  "social_links": "None",
  "location": "SF",
  "service_type": "Tech"
}
```
"""
        result = extract_business_card_from_response(response)

        # Should still extract it
        assert result["has_confirmation"] is True
        assert result["business_card"].name == "Test Co"
