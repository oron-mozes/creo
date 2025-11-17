"""Pydantic models for API requests and responses."""
from typing import Optional
from pydantic import BaseModel


class ChatRequest(BaseModel):
    """Chat request model."""
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    """Chat response model."""
    response: str
    session_id: str


class CreateSessionRequest(BaseModel):
    """Create session request model."""
    message: str


class CreateSessionResponse(BaseModel):
    """Create session response model."""
    session_id: str
    user_id: str


class GetMessagesResponse(BaseModel):
    """Get messages response model."""
    messages: list
    session_id: str


class SuggestionsResponse(BaseModel):
    """Suggestions response model."""
    welcome_message: str
    suggestions: list[str]


class CreateSessionRequestWithUser(BaseModel):
    """Create session request with optional user ID."""
    message: str
    user_id: Optional[str] = None  # For anonymous users


class ChatRequestWithUser(BaseModel):
    """Chat request with optional user ID."""
    message: str
    session_id: Optional[str] = None
    user_id: Optional[str] = None  # For anonymous users


class MigrateUserRequest(BaseModel):
    """Migrate anonymous user request."""
    anonymous_user_id: str


class InfluencerResponseRequest(BaseModel):
    """Influencer response from deep link click."""
    token: str
