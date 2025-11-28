from __future__ import annotations

import uuid
from typing import Any, Callable

from sockets.utils.auth import resolve_user
from sockets.handlers.join_session import handle_join_session
from sockets.handlers.run_agent import run_agent_and_stream
from workflow_enums import MessageRole, SocketEvent


def register_chat_socket_handlers(
    sio: Any,
    session_manager: Any,
    message_store: Any,
    verify_token: Callable[[str], Any],
    get_business_card: Callable[[str], Any],
    root_agent: Any,
) -> None:
    """Register Socket.IO chat event handlers."""

    @sio.event
    async def connect(sid: str, environ: dict[str, Any]) -> None:
        print(f"[SOCKET] Connected: {sid}")

    @sio.event
    async def disconnect(sid: str) -> None:
        print(f"[SOCKET] Disconnected: {sid}")

    @sio.event
    async def join_session(sid: str, data: dict[str, Any]) -> None:
        await handle_join_session(
            sio=sio,
            session_manager=session_manager,
            message_store=message_store,
            get_business_card=get_business_card,
            root_agent=root_agent,
            sid=sid,
            data=data,
            verify_token=verify_token,
            run_agent_and_stream=run_agent_and_stream,
        )

    @sio.event
    async def send_message(sid: str, data: dict[str, Any]) -> None:
        """
        Handle a new user message and stream agent response.
        """
        try:
            message = data.get("message")
            session_id = data.get("session_id")
            token = data.get("token")
            anon_user_id = data.get("user_id")

            user_id, user_profile, is_authenticated = resolve_user(token, anon_user_id, sid, verify_token)
            print(f"[SEND_MESSAGE] sid={sid} session={session_id} user={user_id} token={'yes' if token else 'no'} message='{(message or '')[:80]}...'")

            if not message or not session_id:
                print("[SEND_MESSAGE] ERROR: Missing message or session_id")
                await sio.emit(SocketEvent.ERROR.value, {"error": "Missing message or session_id"}, room=sid)
                return

            # Ensure session exists
            try:
                session_manager.ensure_session(user_id, session_id, user_profile)
            except Exception as e:
                print(f"[SEND_MESSAGE] WARNING: ensure_session failed ({e}), continuing")

            # Persist user message
            message_store.save_message(session_id, MessageRole.USER.value, message, user_id)
            await sio.emit(SocketEvent.AGENT_THINKING.value, {"session_id": session_id}, room=session_id)

            await run_agent_and_stream(
                sio=sio,
                session_manager=session_manager,
                message_store=message_store,
                root_agent=root_agent,
                session_id=session_id,
                user_id=user_id,
                token=token,
                user_profile=user_profile,
                message=message,
                is_authenticated=is_authenticated,
                context_tag="SEND_MESSAGE",
            )

        except Exception as e:
            print(f"Error in send_message: {str(e)}")
            await sio.emit(SocketEvent.ERROR.value, {"error": str(e)}, room=sid)
