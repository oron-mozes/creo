from typing import Any, Callable

from sockets.utils.auth import resolve_user
from services.content import content_to_text
from workflow_enums import MessageRole, SocketEvent


async def handle_join_session(
    sio,
    session_manager,
    message_store,
    get_business_card: Callable[[str], Any],
    root_agent,
    sid: str,
    data: dict,
    verify_token: Callable[[str], Any],
    run_agent_and_stream: Callable[..., Any],
):
    """
    Shared implementation for the Socket.IO join_session handler.
    """
    session_id = data.get("session_id")
    token = data.get("token")
    anon_user_id = data.get("user_id")

    user_id, user_profile, is_authenticated = resolve_user(token, anon_user_id, sid, verify_token)
    print(f"[JOIN_SESSION] sid={sid} session={session_id} user={user_id} token={'yes' if token else 'no'}")

    if not session_id:
        print("[JOIN_SESSION] ERROR: Missing session_id")
        await sio.emit("error", {"error": "Missing session_id"}, room=sid)
        return

    await sio.enter_room(sid, session_id)
    print(f"[JOIN_SESSION] Client {sid} successfully joined session {session_id}")

    # Load business card into memory (if any)
    business_card = get_business_card(user_id)
    session_manager.load_business_card_into_session(session_id, business_card)

    # Send chat history
    messages = message_store.get_session_messages(session_id)
    print(f"[JOIN_SESSION] Sending {len(messages)} messages from chat history to client {sid}")
    await sio.emit(
        SocketEvent.CHAT_HISTORY.value,
        {"messages": messages, "session_id": session_id},
        room=sid,
    )

    # If the last message was from user, auto-process it
    if messages and messages[-1].get("role") == MessageRole.USER.value:
        initial_message = messages[-1]["content"]
        preview = content_to_text(initial_message) if hasattr(initial_message, "parts") else initial_message
        print(f"[JOIN_SESSION] Last message is from user, processing initial message: '{preview[:80]}...'")
        await run_agent_and_stream(
            sio=sio,
            session_manager=session_manager,
            message_store=message_store,
            root_agent=root_agent,
            session_id=session_id,
            user_id=user_id,
            token=token,
            user_profile=user_profile,
            message=initial_message,
            is_authenticated=is_authenticated,
            context_tag="JOIN_SESSION",
        )
