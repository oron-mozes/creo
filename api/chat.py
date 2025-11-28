from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from auth import UserInfo, get_optional_user
from services.content import content_to_text
from session_manager import SessionManager
from google.adk.agents.llm_agent import Agent


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    user_id: Optional[str] = None  # For anonymous users


class ChatResponse(BaseModel):
    response: str
    session_id: str


def build_chat_router(
    session_manager: SessionManager,
    root_agent: Agent,
) -> APIRouter:
    router = APIRouter()

    @router.post("/api/chat", response_model=ChatResponse)
    def chat(
        request: ChatRequest,
        current_user: Optional[UserInfo] = Depends(get_optional_user)
    ) -> ChatResponse:
        """
        Send a message to the orchestrator agent.
        Works for both authenticated and anonymous users.
        """
        try:
            user_profile = None
            if current_user:
                user_id = current_user.user_id
                user_profile = {'name': current_user.name}
                print(f"[CHAT] Authenticated user: {user_id}")
            else:
                user_id = request.user_id or f"anon_{uuid.uuid4().hex[:12]}"
                print(f"[CHAT] Anonymous user: {user_id}")

            session_id = request.session_id or f"session_{uuid.uuid4().hex}"
            final_response = None
            all_responses = []

            session_memory = session_manager.get_session_memory(session_id)
            if session_memory:
                workflow_stage = session_memory.get_workflow_stage()
                has_business_card = session_memory.has_business_card()
                print(f"[SESSION_STATE] Session: {session_id} | Stage: {workflow_stage.value if workflow_stage else 'None'} | Business Card: {'Yes' if has_business_card else 'No'}")

            for event in session_manager.run_agent(
                user_id=user_id,
                session_id=session_id,
                message=request.message,
                user_profile=user_profile
            ):
                if event.author:
                    agent_name = event.author
                    is_final = event.is_final_response()
                    print(f"[AGENT_TRANSITION] → {agent_name} | Session: {session_id} | is_final: {is_final}")

                    if session_memory and is_final:
                        new_stage = session_memory.get_workflow_stage()
                        print(f"[WORKFLOW_STATE] After {agent_name}: stage={new_stage.value if new_stage else 'None'}")

                candidate = content_to_text(event.content)
                if candidate:
                    all_responses.append(candidate)

                if event.author == root_agent.name and event.is_final_response():
                    if candidate:
                        final_response = candidate

            response_text = final_response or "\n".join(all_responses) or "No response generated"
            session_manager.save_assistant_message(session_id, response_text)

            return ChatResponse(
                response=response_text,
                session_id=session_id
            )

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @router.delete("/api/session/{user_id}")
    def clear_session(user_id: str) -> dict:
        """Clear all sessions for a specific user."""
        session_manager.clear_user_sessions(user_id)
        return {"status": "success", "message": f"Sessions cleared for user: {user_id}"}

    return router
