"""Outreach message data models."""
from typing import Optional
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from enum import Enum


class ResponseType(str, Enum):
    """Influencer response types."""
    INTERESTED = "interested"
    NOT_INTERESTED = "not_interested"
    NEED_INFO = "need_info"


class OutreachEmail(BaseModel):
    """Outreach email model for influencer collaboration requests.

    This model captures all information needed to send a personalized
    outreach email to an influencer.
    """

    # Recipient information
    creator_email: EmailStr
    creator_name: str

    # Campaign information from brief
    brand_name: str
    brand_description: str  # Short description like "coffee shop in London"
    platform: str  # Instagram, TikTok, etc.
    location: str
    niche: str
    goal: str  # Campaign goal in 3-5 words
    budget_per_creator: float

    # Session tracking
    session_id: str
    user_id: str

    # Metadata
    sent_at: Optional[datetime] = None
    email_id: Optional[str] = None  # Gmail message ID after sending

    def to_dict(self) -> dict:
        """Convert to dictionary for storage."""
        return {
            "creator_email": self.creator_email,
            "creator_name": self.creator_name,
            "brand_name": self.brand_name,
            "brand_description": self.brand_description,
            "platform": self.platform,
            "location": self.location,
            "niche": self.niche,
            "goal": self.goal,
            "budget_per_creator": self.budget_per_creator,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "email_id": self.email_id,
        }


class InfluencerResponse(BaseModel):
    """Influencer response to outreach email.

    Captures the influencer's response when they click a deep link
    in the outreach email.
    """

    # Response details
    response_type: ResponseType
    creator_email: EmailStr
    creator_name: str

    # Session tracking
    session_id: str
    user_id: str

    # Metadata
    responded_at: datetime = Field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict:
        """Convert to dictionary for storage."""
        return {
            "response_type": self.response_type.value,
            "creator_email": self.creator_email,
            "creator_name": self.creator_name,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "responded_at": self.responded_at.isoformat(),
        }

    def get_user_friendly_message(self) -> str:
        """Get user-friendly message about the response."""
        if self.response_type == ResponseType.INTERESTED:
            return f"✅ {self.creator_name} is interested in your collaboration!"
        elif self.response_type == ResponseType.NOT_INTERESTED:
            return f"❌ {self.creator_name} declined the collaboration opportunity."
        else:  # NEED_INFO
            return f"❓ {self.creator_name} needs more information about the collaboration."
