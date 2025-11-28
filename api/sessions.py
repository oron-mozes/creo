from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from auth import UserInfo, get_optional_user
from services.user_service import UserService
from services.message_store import MessageStore


class CreateSessionRequest(BaseModel):
    message: str
    user_id: Optional[str] = None  # For anonymous users
    session_id: Optional[str] = None  # Optional session_id to use existing session


class CreateSessionResponse(BaseModel):
    session_id: str
    user_id: str


class SessionInfo(BaseModel):
    id: str
    title: str
    timestamp: str


class GetSessionsResponse(BaseModel):
    sessions: list[SessionInfo]


class GetMessagesResponse(BaseModel):
    messages: list
    session_id: str


def build_sessions_router(message_store: MessageStore, user_service: UserService) -> APIRouter:
    router = APIRouter()

    @router.post("/api/sessions", response_model=CreateSessionResponse)
    def create_session(
        request: CreateSessionRequest,
        current_user: Optional[UserInfo] = Depends(get_optional_user)
    ) -> CreateSessionResponse:
        """
        Create a new chat session with an initial message.
        Returns session_id to redirect user to chat page.

        Works for both authenticated and anonymous users.
        If session_id is provided, uses that instead of generating a new one.
        """
        session_id = request.session_id or f"session_{uuid.uuid4().hex}"

        if current_user:
            user_id = current_user.user_id
            print(f"[CREATE_SESSION] Authenticated user: {user_id}")
        else:
            user_id = request.user_id or f"anon_{uuid.uuid4().hex[:12]}"
            print(f"[CREATE_SESSION] Anonymous user: {user_id}")

        print(f"[CREATE_SESSION] session_id={session_id}, user_id={user_id}, message='{request.message[:50]}...'")

        # Persist session owner (but avoid double-saving the first message; sockets will save it)
        message_store.ensure_session(session_id, user_id, first_message=request.message)
        print(f"[CREATE_SESSION] Session registered (owner + metadata only)")

        return CreateSessionResponse(session_id=session_id, user_id=user_id)

    @router.get("/api/sessions", response_model=GetSessionsResponse)
    def get_user_sessions(user_id: str, current_user: Optional[UserInfo] = Depends(get_optional_user)) -> GetSessionsResponse:
        """Get all chat sessions for a user with summaries."""
        print(f"[GET_SESSIONS] Fetching sessions for user {user_id}")

        # If anon ID is already linked to an authenticated user, require auth
        linked_user_id = user_service.get_linked_user_id(user_id)
        if linked_user_id and (not current_user or current_user.user_id != linked_user_id):
            print(f"[GET_SESSIONS] Blocking access for anon_id={user_id} - linked to user {linked_user_id}")
            raise HTTPException(status_code=401, detail="Authentication required")

        # If requesting an authenticated user_id but not logged in, block
        if user_id.startswith("google_") and not current_user:
            raise HTTPException(status_code=401, detail="Authentication required")

        try:
            session_dicts = message_store.get_user_sessions(user_id)
            print(f"[GET_SESSIONS] Found {len(session_dicts)} sessions for user {user_id}")
            session_models = [SessionInfo(**session) for session in session_dicts]
            return GetSessionsResponse(sessions=session_models)
        except Exception as e:
            print(f"[GET_SESSIONS] Error: {e}")
            import traceback
            traceback.print_exc()
            return GetSessionsResponse(sessions=[])

    @router.get("/api/sessions/{session_id}/messages", response_model=GetMessagesResponse)
    def get_messages(session_id: str) -> GetMessagesResponse:
        """Get all messages for a session."""
        print(f"[GET_MESSAGES] Fetching messages for session {session_id}")
        messages = message_store.get_session_messages(session_id)
        print(f"[GET_MESSAGES] Found {len(messages)} messages for session {session_id}")
        return GetMessagesResponse(messages=messages, session_id=session_id)

    return router
