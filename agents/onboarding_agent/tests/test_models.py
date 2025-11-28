"""Unit tests for BusinessCard model."""
import pytest
from agents.onboarding_agent.models import BusinessCard


class TestBusinessCard:
    """Test cases for BusinessCard model."""

    def test_business_card_creation_with_all_fields(self) -> None:
        """Test creating a BusinessCard with all fields provided."""
        card = BusinessCard(
            name="Test Company",
            website="example.com",
            social_links="https://instagram.com/test",
            location="San Francisco, CA",
            service_type="Software Development"
        )

        assert card.name == "Test Company"
        assert card.website == "https://example.com"  # Should add https://
        assert card.social_links == "https://instagram.com/test"
        assert card.location == "San Francisco, CA"
        assert card.service_type == "Software Development"

    def test_business_card_website_url_validation(self) -> None:
        """Test that website URLs are automatically prefixed with https://."""
        # Without protocol
        card = BusinessCard(
            name="Test",
            website="example.com",
            location="City",
            service_type="Service"
        )
        assert card.website == "https://example.com"

        # With http://
        card = BusinessCard(
            name="Test",
            website="http://example.com",
            location="City",
            service_type="Service"
        )
        assert card.website == "http://example.com"

        # With https://
        card = BusinessCard(
            name="Test",
            website="https://example.com",
            location="City",
            service_type="Service"
        )
        assert card.website == "https://example.com"

    def test_business_card_optional_fields(self) -> None:
        """Test BusinessCard with optional fields as None."""
        card = BusinessCard(
            name="Test Company",
            location="San Francisco",
            service_type="Tech"
        )

        assert card.name == "Test Company"
        assert card.website is None
        assert card.social_links is None
        assert card.location == "San Francisco"
        assert card.service_type == "Tech"

    def test_business_card_to_dict(self) -> None:
        """Test converting BusinessCard to dictionary."""
        card = BusinessCard(
            name="Test Company",
            website="https://example.com",
            social_links="https://instagram.com/test",
            location="San Francisco",
            service_type="Tech"
        )

        result = card.to_dict()

        assert result == {
            "name": "Test Company",
            "website": "https://example.com",
            "social_links": "https://instagram.com/test",
            "location": "San Francisco",
            "service_type": "Tech"
        }

    def test_business_card_to_dict_with_none_values(self) -> None:
        """Test to_dict converts None to 'Not provided'."""
        card = BusinessCard(
            name="Test Company",
            location="San Francisco",
            service_type="Tech"
        )

        result = card.to_dict()

        assert result["name"] == "Test Company"
        assert result["website"] == "Not provided"
        assert result["social_links"] == "Not provided"
        assert result["location"] == "San Francisco"
        assert result["service_type"] == "Tech"

    def test_business_card_is_complete_with_website(self) -> None:
        """Test is_complete returns True when all required fields and website are provided."""
        card = BusinessCard(
            name="Test Company",
            website="https://example.com",
            location="San Francisco",
            service_type="Tech"
        )

        assert card.is_complete() is True

    def test_business_card_is_complete_with_social_links(self) -> None:
        """Test is_complete returns True when all required fields and social links are provided."""
        card = BusinessCard(
            name="Test Company",
            social_links="https://instagram.com/test",
            location="San Francisco",
            service_type="Tech"
        )

        assert card.is_complete() is True

    def test_business_card_is_complete_with_both_contact_methods(self) -> None:
        """Test is_complete returns True when both website and social links are provided."""
        card = BusinessCard(
            name="Test Company",
            website="https://example.com",
            social_links="https://instagram.com/test",
            location="San Francisco",
            service_type="Tech"
        )

        assert card.is_complete() is True

    def test_business_card_is_not_complete_missing_name(self) -> None:
        """Test is_complete returns False when name is missing."""
        card = BusinessCard(
            website="https://example.com",
            location="San Francisco",
            service_type="Tech"
        )

        assert card.is_complete() is False

    def test_business_card_is_not_complete_missing_contact(self) -> None:
        """Test is_complete returns False when both website and social links are missing."""
        card = BusinessCard(
            name="Test Company",
            location="San Francisco",
            service_type="Tech"
        )

        assert card.is_complete() is False

    def test_business_card_is_not_complete_missing_location(self) -> None:
        """Test is_complete returns False when location is missing."""
        card = BusinessCard(
            name="Test Company",
            website="https://example.com",
            service_type="Tech"
        )

        assert card.is_complete() is False

    def test_business_card_is_not_complete_missing_service_type(self) -> None:
        """Test is_complete returns False when service_type is missing."""
        card = BusinessCard(
            name="Test Company",
            website="https://example.com",
            location="San Francisco"
        )

        assert card.is_complete() is False

    def test_business_card_not_provided_string_treated_as_missing(self) -> None:
        """Test that 'Not provided' strings are treated as missing values."""
        card = BusinessCard(
            name="Test Company",
            website="Not provided",
            social_links="Not provided",
            location="San Francisco",
            service_type="Tech"
        )

        # Should be incomplete because both contact methods are "Not provided"
        assert card.is_complete() is False
