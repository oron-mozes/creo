"""Firestore database utilities for storing conversations and sessions."""
from __future__ import annotations

import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from google.cloud import firestore
from google.cloud.firestore_v1 import FieldFilter
from pydantic import BaseModel, Field

# Initialize Firestore client
# In Cloud Run, this will automatically use the service account
# Locally, it will use GOOGLE_APPLICATION_CREDENTIALS env var or gcloud auth
_db: Optional[firestore.Client] = None
# Shared in-memory fallback for creator records when Firestore is unavailable
_in_memory_creators: List[Dict[str, Any]] = []


def get_db() -> firestore.Client:
    """Get or create Firestore client."""
    global _db
    if _db is None:
        # Get project ID from environment or use default
        project_id = os.environ.get("GCP_PROJECT_ID", "gen-lang-client-0751221742")
        _db = firestore.Client(project=project_id)
    return _db


# Collection names
CONVERSATIONS = "conversations"
SESSIONS = "sessions"
CAMPAIGNS = "campaigns"
ANALYTICS = "analytics"
CREATORS = "creators"
CREATOR_STATUS_PENDING = "pending"
CREATOR_STATUS_RESPONDED = "responded"
CREATOR_STATUS_BOUNCED = "bounced"


# Pydantic Models for type safety and validation

class Message(BaseModel):
    """Conversation message model."""
    session_id: str
    user_id: str
    role: str  # "user" or "assistant"
    message: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: Optional[datetime] = None
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class Session(BaseModel):
    """User session model."""
    session_id: str
    user_id: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    message_count: int = 0
    created_at: Optional[datetime] = None
    last_activity: Optional[datetime] = None


class Campaign(BaseModel):
    """Campaign data model."""
    user_id: str
    name: Optional[str] = None
    objective: Optional[str] = None
    target_audience: Optional[str] = None
    budget: Optional[float] = None
    timeline: Optional[str] = None
    channels: List[str] = Field(default_factory=list)
    campaign_data: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class AnalyticsEvent(BaseModel):
    """Analytics event model."""
    event_type: str
    user_id: Optional[str] = None
    data: Dict[str, Any] = Field(default_factory=dict)
    timestamp: Optional[datetime] = None
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class Creator(BaseModel):
    """Creator/Influencer model."""
    name: str
    platform: str  # YouTube, Instagram, TikTok, etc.
    category: str  # food, travel, tech, lifestyle, fashion, beauty, fitness, gaming
    location: Optional[str] = None  # geographic location
    subscriber_count: Optional[int] = None
    follower_count: Optional[int] = None  # for non-YouTube platforms
    view_count: Optional[int] = None
    video_count: Optional[int] = None
    engagement_rate: Optional[float] = None  # percentage
    estimated_price_min: Optional[float] = None  # USD
    estimated_price_max: Optional[float] = None  # USD
    description: Optional[str] = None
    channel_url: Optional[str] = None
    profile_url: Optional[str] = None
    tags: List[str] = Field(default_factory=list)  # additional searchable tags
    metadata: Dict[str, Any] = Field(default_factory=dict)  # additional data
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    status: str = CREATOR_STATUS_PENDING
    response: Optional[str] = None
    email: Optional[str] = None
    notes: Optional[str] = None


class CreatorDB:
    """Manage creator records in Firestore."""

    def __init__(self, db: Optional[firestore.Client] = None):
        if db is None:
            try:
                db = get_db()
            except Exception as e:
                print(f"[CreatorDB] Firestore unavailable: {e}")
                db = None

        self.db = db
        self.collection = self.db.collection(CREATORS) if self.db else None

    def save_creators(self, creators: List[Dict[str, Any]], session_id: str, user_id: str) -> None:
        """Save a list of creators for a session with pending status."""
        if not creators:
            return

        payloads = []
        for creator in creators:
            payloads.append(
                {
                    **creator,
                    "session_id": session_id,
                    "user_id": user_id,
                    "status": CREATOR_STATUS_PENDING,
                    "response": None,
                    "created_at": firestore.SERVER_TIMESTAMP if self.collection else datetime.utcnow(),
                    "updated_at": firestore.SERVER_TIMESTAMP if self.collection else datetime.utcnow(),
                }
            )

        if self.collection:
            batch = self.db.batch()
            for payload in payloads:
                doc_ref = self.collection.document()
                batch.set(doc_ref, payload)
            batch.commit()
        else:
            # In-memory fallback shared across CreatorDB instances
            _in_memory_creators.extend(payloads)

    def get_creators_by_session(self, session_id: str) -> List[Dict[str, Any]]:
        """Fetch creators linked to a session."""
        if not self.collection:
            # Return a shallow copy so callers can't mutate the shared store
            return [
                {**creator, "id": str(idx)}
                for idx, creator in enumerate(_in_memory_creators)
                if creator.get("session_id") == session_id
            ]
        docs = (
            self.collection.where(filter=FieldFilter("session_id", "==", session_id))
            .order_by("created_at")
            .stream()
        )
        return [{**doc.to_dict(), "id": doc.id} for doc in docs]

    def update_creator_status(self, creator_id: str, status: str, response: Optional[str] = None) -> None:
        if not self.collection:
            # Update in-memory fallback
            for idx, creator in enumerate(_in_memory_creators):
                if str(idx) == creator_id:
                    creator["status"] = status
                    creator["response"] = response
                    creator["updated_at"] = datetime.utcnow()
            return
        self.collection.document(creator_id).update(
            {
                "status": status,
                "response": response,
                "updated_at": firestore.SERVER_TIMESTAMP,
            }
        )


class ConversationDB:
    """Manage conversation storage in Firestore."""

    def __init__(self):
        self.db = get_db()
        self.collection = self.db.collection(CONVERSATIONS)

    def save_message(
        self,
        session_id: str,
        user_id: str,
        role: str,  # "user" or "assistant"
        message: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Save a conversation message."""
        doc_data = {
            "session_id": session_id,
            "user_id": user_id,
            "role": role,
            "message": message,
            "metadata": metadata or {},
            "timestamp": firestore.SERVER_TIMESTAMP,
            "created_at": datetime.utcnow().isoformat(),
        }

        doc_ref = self.collection.add(doc_data)
        return doc_ref[1].id

    def get_conversation_history(
        self,
        session_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get conversation history for a session."""
        query = (
            self.collection
            .where(filter=FieldFilter("session_id", "==", session_id))
            .order_by("timestamp")
            .limit(limit)
        )

        docs = query.stream()
        return [
            {
                "id": doc.id,
                **doc.to_dict()
            }
            for doc in docs
        ]

    def delete_session(self, session_id: str) -> int:
        """Delete all messages for a session."""
        query = self.collection.where(filter=FieldFilter("session_id", "==", session_id))
        docs = query.stream()

        deleted_count = 0
        batch = self.db.batch()
        for doc in docs:
            batch.delete(doc.reference)
            deleted_count += 1

        if deleted_count > 0:
            batch.commit()

        return deleted_count


class SessionDB:
    """Manage user sessions in Firestore."""

    def __init__(self):
        self.db = get_db()
        self.collection = self.db.collection(SESSIONS)

    def create_session(
        self,
        session_id: str,
        user_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Create a new session."""
        doc_data = {
            "session_id": session_id,
            "user_id": user_id,
            "metadata": metadata or {},
            "created_at": firestore.SERVER_TIMESTAMP,
            "last_activity": firestore.SERVER_TIMESTAMP,
            "message_count": 0,
        }

        self.collection.document(session_id).set(doc_data)

    def update_activity(self, session_id: str) -> None:
        """Update last activity timestamp for a session."""
        self.collection.document(session_id).update({
            "last_activity": firestore.SERVER_TIMESTAMP,
            "message_count": firestore.Increment(1),
        })

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session information."""
        doc = self.collection.document(session_id).get()
        if doc.exists:
            return doc.to_dict()
        return None

    def get_user_sessions(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get all sessions for a user."""
        query = (
            self.collection
            .where(filter=FieldFilter("user_id", "==", user_id))
            .order_by("last_activity", direction=firestore.Query.DESCENDING)
            .limit(limit)
        )

        docs = query.stream()
        return [
            {
                "session_id": doc.id,
                **doc.to_dict()
            }
            for doc in docs
        ]

    def delete_session(self, session_id: str) -> None:
        """Delete a session."""
        self.collection.document(session_id).delete()


class CampaignDB:
    """Manage campaign data in Firestore."""

    def __init__(self):
        self.db = get_db()
        self.collection = self.db.collection(CAMPAIGNS)

    def save_campaign(
        self,
        user_id: str,
        campaign_data: Dict[str, Any],
        campaign_id: Optional[str] = None
    ) -> str:
        """Save a campaign."""
        doc_data = {
            "user_id": user_id,
            "campaign_data": campaign_data,
            "created_at": firestore.SERVER_TIMESTAMP,
            "updated_at": firestore.SERVER_TIMESTAMP,
        }

        if campaign_id:
            self.collection.document(campaign_id).set(doc_data)
            return campaign_id
        else:
            doc_ref = self.collection.add(doc_data)
            return doc_ref[1].id

    def get_campaign(self, campaign_id: str) -> Optional[Dict[str, Any]]:
        """Get a campaign by ID."""
        doc = self.collection.document(campaign_id).get()
        if doc.exists:
            return {
                "id": doc.id,
                **doc.to_dict()
            }
        return None

    def get_user_campaigns(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get all campaigns for a user."""
        query = (
            self.collection
            .where(filter=FieldFilter("user_id", "==", user_id))
            .order_by("created_at", direction=firestore.Query.DESCENDING)
            .limit(limit)
        )

        docs = query.stream()
        return [
            {
                "id": doc.id,
                **doc.to_dict()
            }
            for doc in docs
        ]


class AnalyticsDB:
    """Track analytics and metrics."""

    def __init__(self):
        self.db = get_db()
        self.collection = self.db.collection(ANALYTICS)

    def log_event(
        self,
        event_type: str,
        user_id: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> str:
        """Log an analytics event."""
        doc_data = {
            "event_type": event_type,
            "user_id": user_id,
            "data": data or {},
            "timestamp": firestore.SERVER_TIMESTAMP,
            "created_at": datetime.utcnow().isoformat(),
        }

        doc_ref = self.collection.add(doc_data)
        return doc_ref[1].id

    def get_events(
        self,
        event_type: Optional[str] = None,
        user_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get analytics events with optional filtering."""
        query = self.collection

        if event_type:
            query = query.where(filter=FieldFilter("event_type", "==", event_type))
        if user_id:
            query = query.where(filter=FieldFilter("user_id", "==", user_id))

        query = query.order_by("timestamp", direction=firestore.Query.DESCENDING).limit(limit)

        docs = query.stream()
        return [
            {
                "id": doc.id,
                **doc.to_dict()
            }
            for doc in docs
        ]
