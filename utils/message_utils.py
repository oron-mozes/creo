"""Firestore/in-memory utilities for messages, business cards, campaign briefs, and creators."""
import uuid
import importlib
from typing import Optional, List, Dict, Any, cast
from datetime import datetime
from config.database import get_db
from db import CreatorDB, _in_memory_creators

firestore: Any
try:
    firestore = importlib.import_module("google.cloud.firestore")
except Exception:
    firestore = None


# In-memory storage for local development (when Firestore is not available)
in_memory_messages: Dict[str, List[Dict[str, Any]]] = {}
in_memory_business_cards: Dict[str, Dict[str, Any]] = {}
in_memory_campaign_briefs: Dict[str, Dict[str, Any]] = {}
# Alias to CreatorDB in-memory store for visibility in tests/dev
in_memory_creators = _in_memory_creators


def save_message_to_firestore(session_id: str, role: str, content: str, user_id: Optional[str] = None) -> str:
    """Save a message to Firestore or in-memory storage.

    Args:
        session_id: Session identifier
        role: Message role (user/assistant)
        content: Message content
        user_id: Optional user identifier

    Returns:
        Message ID
    """
    db = get_db()

    if db is not None and firestore is not None:
        # Use Firestore
        message_ref = db.collection('sessions').document(session_id).collection('messages').document()
        message_data = {
            'role': role,
            'content': content,
            'timestamp': firestore.SERVER_TIMESTAMP,
            'user_id': user_id
        }
        message_ref.set(message_data)
        return cast(str, message_ref.id)
    else:
        # Use in-memory storage for local development
        if session_id not in in_memory_messages:
            in_memory_messages[session_id] = []

        message_data = {
            'id': str(uuid.uuid4()),
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat(),
            'user_id': user_id
        }
        in_memory_messages[session_id].append(message_data)
        return cast(str, message_data['id'])


def get_session_messages(session_id: str) -> List[Dict[str, Any]]:
    """Get all messages for a session from Firestore or in-memory storage.

    Args:
        session_id: Session identifier

    Returns:
        List of message dictionaries
    """
    db = get_db()

    if db is not None and firestore is not None:
        # Use Firestore
        messages_ref = db.collection('sessions').document(session_id).collection('messages')
        messages = messages_ref.order_by('timestamp').stream()

        result = []
        for msg in messages:
            msg_data = msg.to_dict()
            timestamp = msg_data.get('timestamp')
            # Convert Firestore DatetimeWithNanoseconds to ISO format string
            timestamp_str = timestamp.isoformat() if timestamp else None
            result.append({
                'id': msg.id,
                'role': msg_data.get('role'),
                'content': msg_data.get('content'),
                'timestamp': timestamp_str,
                'user_id': msg_data.get('user_id')
            })
        return result
    else:
        # Use in-memory storage for local development
        return in_memory_messages.get(session_id, [])


def search_conversation_history(session_id: str, query: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
    """Search conversation history for RAG.

    This function can be used as a tool by the orchestrator agent.

    Args:
        session_id: Session identifier
        query: Optional search query (not implemented yet)
        limit: Maximum number of messages to return

    Returns:
        List of recent messages
    """
    messages = get_session_messages(session_id)

    # If query provided, you could implement semantic search here
    # For now, just return recent messages
    return messages[-limit:] if len(messages) > limit else messages


def get_user_past_sessions(user_id: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Get past sessions for a user with brief summaries.

    Args:
        user_id: The user identifier
        limit: Maximum number of sessions to return

    Returns:
        List of session summaries with session_id and first message
    """
    db = get_db()

    if db is not None and firestore is not None:
        # Use Firestore
        # This is a simplified version - in production you'd query Firestore properly
        return []
    else:
        # Use in-memory storage
        past_sessions = []
        for session_id, messages in in_memory_messages.items():
            if messages and len(messages) > 0:
                first_user_msg = next((msg for msg in messages if msg.get('role') == 'user'), None)
                if first_user_msg:
                    past_sessions.append({
                        'session_id': session_id,
                        'first_message': first_user_msg.get('content', '')[:100],  # First 100 chars
                        'timestamp': first_user_msg.get('timestamp')
                    })
        # Sort by timestamp descending and limit
        past_sessions.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        return past_sessions[:limit]


def save_business_card(user_id: str, business_card_data: Dict[str, Any]) -> None:
    """Save business card data to Firestore or in-memory storage.

    Args:
        user_id: User identifier
        business_card_data: Business card information dictionary
    """
    db = get_db()

    print(f"[BUSINESS_CARD] save_business_card() called for user: {user_id}")
    print(f"[BUSINESS_CARD] Data to save: {business_card_data}")

    if db is not None and firestore is not None:
        # Use Firestore - store in users collection
        user_ref = db.collection('users').document(user_id)
        user_ref.set({
            'business_card': business_card_data,
            'updated_at': firestore.SERVER_TIMESTAMP
        }, merge=True)
        print(f"[BUSINESS_CARD] ✓ Successfully saved to Firestore for user: {user_id}")
    else:
        # Use in-memory storage for local development
        in_memory_business_cards[user_id] = business_card_data
        print(f"[BUSINESS_CARD] ✓ Successfully saved to in-memory storage for user: {user_id}")
        print(f"[BUSINESS_CARD] Current in-memory storage contains {len(in_memory_business_cards)} business cards")


def get_business_card(user_id: str) -> Optional[Dict[str, Any]]:
    """Get business card data from Firestore or in-memory storage.

    Args:
        user_id: User identifier

    Returns:
        Business card data dictionary or None if not found
    """
    db = get_db()

    print(f"[BUSINESS_CARD] get_business_card() called for user: {user_id}")

    if db is not None and firestore is not None:
        # Use Firestore
        print(f"[BUSINESS_CARD] Querying Firestore for user: {user_id}")
        user_ref = db.collection('users').document(user_id)
        user_doc = user_ref.get()
        if user_doc.exists:
            user_data = cast(Dict[str, Any], user_doc.to_dict())
            business_card = user_data.get('business_card')
            if business_card:
                print(f"[BUSINESS_CARD] ✓ Found in Firestore: {business_card.get('name')}")
                return cast(Dict[str, Any], business_card)
        print(f"[BUSINESS_CARD] ℹ Not found in Firestore for user: {user_id}")
        return None
    else:
        # Use in-memory storage for local development
        print(f"[BUSINESS_CARD] Querying in-memory storage (contains {len(in_memory_business_cards)} cards)")
        business_card = in_memory_business_cards.get(user_id)
        if business_card:
            print(f"[BUSINESS_CARD] ✓ Found in in-memory: {business_card.get('name')}")
        else:
            print(f"[BUSINESS_CARD] ℹ Not found in in-memory for user: {user_id}")
        return business_card


def save_campaign_brief(user_id: str, session_id: str, brief_data: Dict[str, Any]) -> None:
    """Save campaign brief data to Firestore or in-memory storage."""
    db = get_db()

    print(f"[CAMPAIGN_BRIEF] save_campaign_brief() called for user: {user_id}, session: {session_id}")
    print(f"[CAMPAIGN_BRIEF] Data to save: {brief_data}")

    if db is not None and firestore is not None:
        session_ref = db.collection('sessions').document(session_id)
        session_ref.set(
            {
                'campaign_brief': brief_data,
                'updated_at': firestore.SERVER_TIMESTAMP,
                'user_id': user_id,
            },
            merge=True,
        )
        print(f"[CAMPAIGN_BRIEF] ✓ Successfully saved to Firestore for session: {session_id}")
    else:
        in_memory_campaign_briefs[session_id] = brief_data
        print(f"[CAMPAIGN_BRIEF] ✓ Saved to in-memory storage for session: {session_id}")


def get_campaign_brief(session_id: str) -> Optional[Dict[str, Any]]:
    """Get campaign brief data from Firestore or in-memory storage."""
    db = get_db()

    print(f"[CAMPAIGN_BRIEF] get_campaign_brief() called for session: {session_id}")

    if db is not None and firestore is not None:
        session_ref = db.collection('sessions').document(session_id)
        session_doc = session_ref.get()
        if session_doc.exists:
            data = cast(Dict[str, Any], session_doc.to_dict() or {})
            brief = data.get('campaign_brief')
            if brief:
                print(f"[CAMPAIGN_BRIEF] ✓ Found in Firestore for session: {session_id}")
                return cast(Dict[str, Any], brief)
        print(f"[CAMPAIGN_BRIEF] ℹ Not found in Firestore for session: {session_id}")
        return None
    else:
        brief = in_memory_campaign_briefs.get(session_id)
        if brief:
            print(f"[CAMPAIGN_BRIEF] ✓ Found in in-memory for session: {session_id}")
            return brief
        print(f"[CAMPAIGN_BRIEF] ℹ Not found in in-memory for session: {session_id}")
        return None


# Creator helpers (delegate to CreatorDB)

def save_creators_for_session(creators: List[Dict[str, Any]], session_id: str, user_id: str) -> None:
    """Save creators for a session using CreatorDB (Firestore or in-memory)."""
    creator_db = CreatorDB(get_db())
    creator_db.save_creators(creators, session_id=session_id, user_id=user_id)


def get_creators_for_session(session_id: str) -> List[Dict[str, Any]]:
    """Get creators for a session using CreatorDB (Firestore or in-memory)."""
    creator_db = CreatorDB(get_db())
    return creator_db.get_creators_by_session(session_id)
