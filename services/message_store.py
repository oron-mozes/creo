"""Message storage helpers for Firestore or in-memory fallback."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

try:
    from google.cloud import firestore
except Exception:  # pragma: no cover - firestore optional in local dev
    firestore = None


class MessageStore:
    """Persist messages either to Firestore or in-memory for development."""

    def __init__(self, db):
        self.db = db
        self._in_memory_messages: Dict[str, List[Dict[str, Any]]] = {}

    def _set_session_owner(self, session_id: str, owner_id: Optional[str]) -> None:
        """Ensure session doc records the owner (anon or authenticated)."""
        if not self.db:
            return
        self.db.collection("sessions").document(session_id).set(
            {
                "user_id": owner_id,
                "owner_id": owner_id,
                "last_activity": firestore.SERVER_TIMESTAMP if firestore else datetime.now(),
                "created_at": firestore.SERVER_TIMESTAMP if firestore else datetime.now(),
            },
            merge=True,
        )

    def ensure_session(
        self,
        session_id: str,
        owner_id: Optional[str],
        first_message: Optional[str] = None,
    ) -> None:
        """Create or update a session document without saving chat messages.

        Used when a client wants to register a session up front (e.g., before
        sending the first message over websockets) to avoid double-saving the
        initial message.
        """
        if not self.db:
            # In-memory: nothing to do until messages arrive
            return

        data = {
            "user_id": owner_id,
            "owner_id": owner_id,
            "last_activity": firestore.SERVER_TIMESTAMP if firestore else datetime.now(),
            "created_at": firestore.SERVER_TIMESTAMP if firestore else datetime.now(),
        }
        if first_message:
            data["first_message"] = first_message

        self.db.collection("sessions").document(session_id).set(data, merge=True)

    def save_message(
        self,
        session_id: str,
        role: str,
        content: str,
        user_id: Optional[str] = None,
    ) -> str:
        """Save a message to storage."""
        if self.db is not None:
            self._set_session_owner(session_id, user_id)
            message_data = {
                'role': role,
                'content': content,
                'timestamp': firestore.SERVER_TIMESTAMP if firestore else datetime.now(),
                'user_id': user_id,
                'owner_id': user_id,
                'session_id': session_id,
            }

            message_ref = self.db.collection('sessions').document(session_id).collection('messages').document()
            message_ref.set(message_data)
            self.db.collection('messages').document(message_ref.id).set(message_data)
            return message_ref.id

        # In-memory fallback for local development
        if session_id not in self._in_memory_messages:
            self._in_memory_messages[session_id] = []

        message_data = {
            'id': str(uuid.uuid4()),
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat(),
            'user_id': user_id,
            'session_id': session_id,
        }
        self._in_memory_messages[session_id].append(message_data)
        return message_data['id']

    def get_session_messages(self, session_id: str) -> list:
        """Return all messages for a session."""
        if self.db is not None:
            messages_ref = self.db.collection('sessions').document(session_id).collection('messages')
            messages = messages_ref.order_by('timestamp').stream()

            result = []
            for msg in messages:
                msg_data = msg.to_dict()
                timestamp = msg_data.get('timestamp')
                timestamp_str = timestamp.isoformat() if timestamp else None
                result.append({
                    'id': msg.id,
                    'role': msg_data.get('role'),
                    'content': msg_data.get('content'),
                    'timestamp': timestamp_str,
                    'user_id': msg_data.get('user_id')
                })
            return result

        return self._in_memory_messages.get(session_id, [])

    def search_conversation_history(self, session_id: str, query: str | None = None, limit: int = 10) -> list:
        """Search (or fetch recent) conversation history."""
        messages = self.get_session_messages(session_id)
        return messages[-limit:] if len(messages) > limit else messages

    def get_user_sessions(self, user_id: str) -> list:
        """Return session summaries for a user/owner."""
        sessions = []

        if self.db is not None:
            session_query = self.db.collection('sessions').where('owner_id', '==', user_id)
            if firestore:
                session_query = session_query.order_by('last_activity', direction=firestore.Query.DESCENDING)
            session_query = session_query.limit(100)
            session_docs = session_query.stream()

            for doc in session_docs:
                data = doc.to_dict()
                timestamp = data.get('last_activity') or data.get('created_at') or datetime.now()
                timestamp_str = timestamp.isoformat() if hasattr(timestamp, "isoformat") else str(timestamp)
                sessions.append(
                    {
                        'id': doc.id,
                        'title': data.get('title') or data.get('first_message') or 'New Chat',
                        'timestamp': timestamp_str,
                        'first_message': data.get('first_message', ''),
                    }
                )

            # Fallback to legacy message scan if no session docs are found
            if not sessions:
                messages_ref = self.db.collection('messages')
                direction = firestore.Query.DESCENDING if firestore else "DESCENDING"
                query = (
                    messages_ref.where('owner_id', '==', user_id)
                    .order_by('timestamp', direction=direction)
                    .limit(100)
                )
                docs = query.stream()

                session_map: Dict[str, Dict[str, Any]] = {}
                for doc in docs:
                    data = doc.to_dict()
                    session_id = data.get('session_id')
                    if session_id and session_id not in session_map:
                        content = data.get('content', '')
                        title = content[:50] if data.get('role') == 'user' else 'New Chat'
                        timestamp = data.get('timestamp', datetime.now())
                        timestamp_str = timestamp.isoformat() if hasattr(timestamp, "isoformat") else str(timestamp)
                        session_map[session_id] = {
                            'id': session_id,
                            'title': title or 'New Chat',
                            'timestamp': timestamp_str,
                            'first_message': content
                        }

                sessions = sorted(session_map.values(), key=lambda s: s['timestamp'], reverse=True)
            return sessions

        # In-memory fallback
        for session_id, msgs in self._in_memory_messages.items():
            if msgs:
                user_msgs = [m for m in msgs if m.get('user_id') == user_id]
                if user_msgs:
                    first_user_msg = next((m for m in msgs if m.get('role') == 'user'), None)
                    title = first_user_msg['content'][:50] if first_user_msg else 'New Chat'
                    timestamp = msgs[0].get('timestamp', datetime.now().isoformat())
                    sessions.append({
                        'id': session_id,
                        'title': title,
                        'timestamp': timestamp,
                        'first_message': first_user_msg.get('content') if first_user_msg else ''
                    })

        return sorted(sessions, key=lambda s: s['timestamp'], reverse=True)

    def migrate_owner_ids(self, old_owner_id: str, new_owner_id: str) -> None:
        """Reassign all sessions and messages from an anon to an authenticated user."""
        if not self.db:
            # In-memory fallback: rewrite messages
            for session_id, msgs in self._in_memory_messages.items():
                for msg in msgs:
                    if msg.get('user_id') == old_owner_id:
                        msg['user_id'] = new_owner_id
                        msg['owner_id'] = new_owner_id
            return

        # Update session documents
        sessions_query = self.db.collection('sessions').where('owner_id', '==', old_owner_id).stream()
        batch = self.db.batch()
        for doc in sessions_query:
            batch.update(
                doc.reference,
                {
                    'owner_id': new_owner_id,
                    'user_id': new_owner_id,
                    'migrated_at': firestore.SERVER_TIMESTAMP if firestore else datetime.now(),
                },
            )
        batch.commit()

        # Update top-level messages collection
        messages_query = self.db.collection('messages').where('owner_id', '==', old_owner_id).stream()
        batch = self.db.batch()
        for doc in messages_query:
            batch.update(
                doc.reference,
                {
                    'owner_id': new_owner_id,
                    'user_id': new_owner_id,
                },
            )
        batch.commit()

        # Update nested session messages
        sessions_to_scan = self.db.collection('sessions').where('owner_id', '==', new_owner_id).stream()
        for session_doc in sessions_to_scan:
            messages_ref = session_doc.reference.collection('messages')
            nested_msgs = messages_ref.where('owner_id', '==', old_owner_id).stream()
            batch = self.db.batch()
            for msg in nested_msgs:
                batch.update(
                    msg.reference,
                    {
                        'owner_id': new_owner_id,
                        'user_id': new_owner_id,
                    },
                )
            batch.commit()

    def get_user_past_sessions(self, user_id: str, limit: int = 5) -> list:
        """Get recent sessions for personalization."""
        sessions = self.get_user_sessions(user_id)
        return sessions[:limit]
