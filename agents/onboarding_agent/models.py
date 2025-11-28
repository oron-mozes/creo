"""Data models for business card information."""
from typing import Optional
from pydantic import BaseModel, HttpUrl, field_validator


class BusinessCard(BaseModel):
    """Business card information model."""
    name: Optional[str] = None
    website: Optional[str] = None
    social_links: Optional[str] = None  # Comma-separated social media URLs
    location: Optional[str] = None
    service_type: Optional[str] = None

    @field_validator('website')
    @classmethod
    def validate_website(cls, v: Optional[str]) -> Optional[str]:
        """Validate website URL format."""
        if v and v != "Not provided":
            # Ensure URL has protocol
            if not v.startswith(('http://', 'https://')):
                v = 'https://' + v
        return v

    def to_dict(self) -> dict[str, str]:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name or "Not provided",
            "website": self.website or "Not provided",
            "social_links": self.social_links or "Not provided",
            "location": self.location or "Not provided",
            "service_type": self.service_type or "Not provided"
        }

    def is_complete(self) -> bool:
        """Check if all required fields are provided.

        Note: Website and social_links are now OPTIONAL - at least one should be provided,
        but not both are required. Essential fields are name, location, and service_type.
        """
        has_contact = (
            (self.website and self.website != "Not provided") or
            (self.social_links and self.social_links != "Not provided")
        )

        return all([
            self.name and self.name != "Not provided",
            has_contact,  # At least website OR social_links
            self.location and self.location != "Not provided",
            self.service_type and self.service_type != "Not provided"
        ])
