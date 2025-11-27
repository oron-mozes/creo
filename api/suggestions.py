from __future__ import annotations

import json
import re
import uuid
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from auth import UserInfo, get_optional_user
from services.message_store import MessageStore
from services.user_service import UserService
from utils.message_utils import get_business_card
from services.content import content_to_text
from google.adk.runners import InMemoryRunner
from google.genai import types


class SuggestionsRequest(BaseModel):
    user_id: Optional[str] = None


class SuggestionsResponse(BaseModel):
    welcome_message: str
    suggestions: list[str]


def build_suggestions_router(
    suggestions_agent,
    message_store: MessageStore,
    user_service: UserService,
) -> APIRouter:
    router = APIRouter()

    @router.post("/api/suggestions", response_model=SuggestionsResponse)
    def get_suggestions(
        request: SuggestionsRequest,
        current_user: Optional[UserInfo] = Depends(get_optional_user)
    ):
        """
        Get personalized welcome message and campaign suggestions for a user.

        Authentication is optional - logged-out users get generic suggestions.
        """
        if not suggestions_agent:
            # Fallback to default suggestions if agent not available
            return SuggestionsResponse(
                welcome_message="Hey! 👋 I'm here to help you connect with amazing influencers. Just tell me what you're looking for, and I'll find the perfect match for your business!",
                suggestions=[
                    "I have a local coffee shop",
                    "I sell handmade jewelry online",
                    "I run a small gym",
                    "I own a boutique hotel"
                ]
            )

        try:
            # Resolve user_id (auth or anon)
            if current_user:
                user_id = current_user.user_id
                user_name = current_user.name
            else:
                user_id = request.user_id
                user_name = None

            if not user_id:
                return SuggestionsResponse(
                    welcome_message="Hey! 👋 I'm here to help you connect with amazing influencers. Just tell me what you're looking for, and I'll find the perfect match for your business!",
                    suggestions=[
                        "I have a local coffee shop",
                        "I sell handmade jewelry online",
                        "I run a small gym",
                        "I own a boutique hotel"
                    ]
                )

            business_card = get_business_card(user_id)
            print(f"[SUGGESTIONS] Business card for user {user_id}: {business_card}")

            linked_user_id = user_service.get_linked_user_id(user_id)
            if linked_user_id and (not current_user or current_user.user_id != linked_user_id):
                past_sessions = []
            else:
                past_sessions = message_store.get_user_past_sessions(user_id, limit=5)
            print(f"[SUGGESTIONS] Past sessions for user {user_id}: {len(past_sessions)}")

            context_parts = []

            if business_card:
                context_parts.append(f"Business Card Information:\n{json.dumps(business_card, indent=2)}")
            else:
                context_parts.append("Business Card: None (not collected yet)")

            if past_sessions:
                context_parts.append(f"\nPast Sessions ({len(past_sessions)}):")
                for i, session in enumerate(past_sessions, 1):
                    context_parts.append(f"{i}. Session {session['id'][:8]}... - First message: {session.get('first_message', '')}")
            else:
                context_parts.append("\nPast Sessions: None (new user)")

            context = "\n".join(context_parts)

            temp_session_id = f"temp_suggestions_{uuid.uuid4().hex}"
            runner = InMemoryRunner(agent=suggestions_agent, app_name="agents")
            session_service = runner.session_service
            if hasattr(session_service, "get_session_sync") and hasattr(session_service, "create_session_sync"):
                existing = session_service.get_session_sync(
                    app_name=runner.app_name, user_id=user_id, session_id=temp_session_id
                )
                if not existing:
                    session_service.create_session_sync(
                        app_name=runner.app_name, user_id=user_id, session_id=temp_session_id
                    )
            elif hasattr(session_service, "create_session_sync"):
                session_service.create_session_sync(
                    app_name=runner.app_name, user_id=user_id, session_id=temp_session_id
                )

            def _ensure_temp_session():
                session_service_local = runner.session_service
                if hasattr(session_service_local, "get_session_sync") and hasattr(session_service_local, "create_session_sync"):
                    existing = session_service_local.get_session_sync(
                        app_name=runner.app_name, user_id=user_id, session_id=temp_session_id
                    )
                    if not existing:
                        session_service_local.create_session_sync(
                            app_name=runner.app_name, user_id=user_id, session_id=temp_session_id
                        )
                elif hasattr(session_service_local, "create_session_sync"):
                    session_service_local.create_session_sync(
                        app_name=runner.app_name, user_id=user_id, session_id=temp_session_id
                    )

            _ensure_temp_session()

            new_message = types.Content(
                role="user",
                parts=[types.Part(text=f"Generate welcome message and campaign suggestions based on:\n\n{context}")],
            )

            def _run_suggestions():
                text = ""
                for event in runner.run(
                    user_id=user_id,
                    session_id=temp_session_id,
                    new_message=new_message,
                ):
                    candidate = content_to_text(event.content)
                    if candidate:
                        text += candidate
                return text

            try:
                response_text = _run_suggestions()
            except ValueError as e:
                if "Session not found" in str(e):
                    print(f"[SUGGESTIONS] Session not found, recreating temp session and retrying: {temp_session_id}")
                    _ensure_temp_session()
                    response_text = _run_suggestions()
                else:
                    raise

            print(f"[SUGGESTIONS] Agent response: {response_text[:200]}...")

            try:
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                json_str = json_match.group(0) if json_match else response_text
                suggestions_data = json.loads(json_str)

                welcome_message = suggestions_data.get("welcome_message", "Hey! 👋 I'm here to help you connect with amazing influencers. Just tell me what you're looking for, and I'll find the perfect match for your business!")
                suggestions = suggestions_data.get("suggestions", [])

                if len(suggestions) < 4:
                    defaults = [
                        "I have a local coffee shop",
                        "I sell handmade jewelry online",
                        "I run a small gym",
                        "I own a boutique hotel"
                    ]
                    suggestions.extend(defaults[len(suggestions):4])
                elif len(suggestions) > 4:
                    suggestions = suggestions[:4]

                return SuggestionsResponse(
                    welcome_message=welcome_message,
                    suggestions=suggestions
                )
            except json.JSONDecodeError as e:
                print(f"[SUGGESTIONS] Error parsing JSON: {e}")
                print(f"[SUGGESTIONS] Response was: {response_text}")
                return SuggestionsResponse(
                    welcome_message="Hey! 👋 I'm here to help you connect with amazing influencers. Just tell me what you're looking for, and I'll find the perfect match for your business!",
                    suggestions=[
                        "I have a local coffee shop",
                        "I sell handmade jewelry online",
                        "I run a small gym",
                        "I own a boutique hotel"
                    ]
                )

        except Exception as e:
            print(f"[SUGGESTIONS] Error: {e}")
            import traceback
            traceback.print_exc()
            return SuggestionsResponse(
                welcome_message="Hey! 👋 I'm here to help you connect with amazing influencers. Just tell me what you're looking for, and I'll find the perfect match for your business!",
                suggestions=[
                    "I have a local coffee shop",
                    "I sell handmade jewelry online",
                    "I run a small gym",
                    "I own a boutique hotel"
                ]
            )

    return router
