from __future__ import annotations

import uuid
from typing import Any, Dict, List, Tuple

from agents.utils import AgentName
from services.content import content_to_text
from workflow_enums import WorkflowStage, MessageRole, SocketEvent
from sockets.utils.gates import should_prompt_login


def _log_session_state(session_id: str, session_memory: Any) -> None:
    if not session_memory:
        return
    stage = session_memory.get_workflow_stage()
    has_business_card = session_memory.has_business_card()
    print(f"[SESSION_STATE] Session: {session_id} | Stage: {stage.value if stage else 'None'} | Business Card: {'Yes' if has_business_card else 'No'}")


def _stream_frontdesk_chunk(sio: Any, session_id: str, message_id: str, chunk: str) -> None:
    """Stream a frontdesk chunk to the client."""
    sio.start_background_task(
        sio.emit,
        SocketEvent.MESSAGE_CHUNK.value,
        {"chunk": chunk, "session_id": session_id, "message_id": message_id},
        room=session_id,
    )


def _record_agent_event(session_memory: Any, agent_name: str, content: str, is_final: bool) -> None:
    """Persist raw agent chunk into session memory for auditing."""
    if session_memory:
        session_memory.add_agent_event(agent_name, content, is_final=is_final)


def _handle_frontdesk_chunk(chunk: str, author: str, sio: Any, session_id: str, message_id: str, response_chunks: List[str]) -> None:
    """Stream and record frontdesk chunks; ignore others."""
    if author != AgentName.FRONTDESK_AGENT.value or not chunk:
        return
    response_chunks.append(chunk)
    _stream_frontdesk_chunk(sio, session_id, message_id, chunk)


def _handle_root_final(
    author: str,
    is_final_event: bool,
    final_text: str,
    session_manager: Any,
    session_id: str,
    user_id: str,
    is_authenticated: bool,
    message_store: Any,
    message_id: str,
    sio: Any,
    root_agent: Any,
) -> bool:
    if author != root_agent.name or not is_final_event or not final_text:
        return False

    session_memory_local = session_manager.get_session_memory(session_id)
    stage = session_memory_local.get_workflow_stage() if session_memory_local else None
    has_brief = False
    if session_memory_local:
        brief_ctx = session_memory_local.get_agent_context("campaign_brief_agent")
        has_brief = bool(brief_ctx and brief_ctx.get("brief"))

    # Check if implicit login gate applies
    if should_prompt_login(stage, has_brief, is_authenticated):
        login_prompt = (
            "Please sign in to continue. We need your email to contact creators and share replies. "
            "Click \"Sign In\" to proceed."
        )
        message_id_login = str(uuid.uuid4())
        message_store.save_message(session_id, MessageRole.ASSISTANT.value, login_prompt, user_id)
        session_manager.save_assistant_message(session_id, login_prompt, message_id_login)
        sio.start_background_task(
            sio.emit,
            SocketEvent.MESSAGE_COMPLETE.value,
            {
                "message": login_prompt,
                "session_id": session_id,
                "message_id": message_id_login,
                "auth_required": True,
                "widget": "auth_signin",
            },
            room=session_id,
        )
        return True

    # Check if explicit tool-triggered auth is required
    auth_triggered = False
    if session_memory_local:
        metadata = session_memory_local.get_shared_context().get("metadata", {})
        print(f"[RUN_AGENT] Checking auth_required_triggered flag. Metadata: {metadata}")
        if metadata.get("auth_required_triggered"):
            auth_triggered = True
            print(f"[RUN_AGENT] Auth required flag detected! is_authenticated={is_authenticated}")
            # Clear the flag so it doesn't persist
            metadata["auth_required_triggered"] = False

    if auth_triggered and not is_authenticated:
        print(f"[RUN_AGENT] Emitting MESSAGE_COMPLETE with auth_required=True and widget='auth_signin'")
        # Use the agent's response as the message, but attach auth_required=True
        message_store.save_message(session_id, MessageRole.ASSISTANT.value, final_text, user_id)
        session_manager.save_assistant_message(session_id, final_text, message_id)
        sio.start_background_task(
            sio.emit,
            SocketEvent.MESSAGE_COMPLETE.value,
            {
                "message": final_text,
                "session_id": session_id,
                "message_id": message_id,
                "auth_required": True,
                "widget": "auth_signin",
            },
            room=session_id,
        )
        return True

    business_card_data = None
    if session_memory_local:
        bc = session_memory_local.get_business_card()
        if bc:
            business_card_data = bc

    message_store.save_message(session_id, MessageRole.ASSISTANT.value, final_text, user_id)
    session_manager.save_assistant_message(session_id, final_text, message_id)

    sio.start_background_task(
        sio.emit,
        SocketEvent.MESSAGE_COMPLETE.value,
        {
            "message": final_text,
            "session_id": session_id,
            "message_id": message_id,
            "business_card": business_card_data,
        },
        room=session_id,
    )
    return True


async def run_agent_and_stream(
    sio: Any,
    session_manager: Any,
    message_store: Any,
    root_agent: Any,
    session_id: str,
    user_id: str,
    token: str | None,
    user_profile: dict | None,
    message: str,
    is_authenticated: bool,
    context_tag: str,
) -> None:
    """
    Run the orchestrator for a message and stream back chunks and the final reply.

    Responsibilities:
    - Call session_manager.run_agent and stream frontdesk chunks only.
    - Record raw agent chunks into session memory for auditing.
    - Apply auth gating (login prompt) before exposing creator/outreach stages.
    - Persist assistant messages to storage.
    - Fallback gracefully when no final response is emitted.
    """
    response_chunks: List[str] = []
    all_chunks: List[Tuple[str, str]] = []
    message_id = str(uuid.uuid4())
    got_final_response = False

    session_memory = session_manager.get_session_memory(session_id)
    _log_session_state(session_id, session_memory)

    for event in session_manager.run_agent(
        user_id=user_id,
        session_id=session_id,
        message=message,
        user_profile=user_profile,
    ):
        # Process streaming content
        chunk = content_to_text(event.content)
        author = str(getattr(event, "author", "") or "")
        is_final_event = bool(getattr(event, "is_final_response", lambda: False)())

        if chunk:
            all_chunks.append((author, chunk))
            _record_agent_event(session_memory, author, chunk, is_final_event)
            _handle_frontdesk_chunk(chunk, author, sio, session_id, message_id, response_chunks)

        got_final_response = _handle_root_final(
            author=author,
            is_final_event=is_final_event,
            final_text=content_to_text(event.content),
            session_manager=session_manager,
            session_id=session_id,
            user_id=user_id,
            is_authenticated=is_authenticated,
            message_store=message_store,
            message_id=message_id,
            sio=sio,
            root_agent=root_agent,
        )
        if got_final_response:
            break

    if not got_final_response:
        # Check if we have a saved frontdesk response in metadata (fallback for empty Orchestrator response)
        session_memory = session_manager.get_session_memory(session_id)
        last_response = None
        if session_memory:
            metadata = session_memory.get_shared_context().get("metadata", {})
            last_response = metadata.get("last_frontdesk_response")

        if last_response:
            print(f"[run_agent] Using saved frontdesk response as fallback: {last_response[:50]}...")
            # Emit the saved response as if it were the final message
            message_store.save_message(session_id, MessageRole.ASSISTANT.value, last_response, user_id)
            session_manager.save_assistant_message(session_id, last_response, message_id)
            await sio.emit(
                SocketEvent.MESSAGE_COMPLETE.value,
                {"message": last_response, "session_id": session_id, "message_id": message_id},
                room=session_id,
            )
        else:
            await _emit_fallback_response(
                sio=sio,
                session_id=session_id,
                message_id=message_id,
                message_store=message_store,
                session_manager=session_manager,
                user_id=user_id,
                response_chunks=response_chunks,
                all_chunks=all_chunks,
            )


async def _emit_fallback_response(
    sio: Any,
    session_id: str,
    message_id: str,
    message_store: Any,
    session_manager: Any,
    user_id: str,
    response_chunks: list[str],
    all_chunks: list[tuple[str, str]],
) -> None:
    """
    Emit a best-effort response when no final/root response was produced.
    Prefers stitched frontdesk chunks; otherwise stitched all-agent chunks.
    """
    if response_chunks:
        final_text = "".join(response_chunks)
        message_store.save_message(session_id, MessageRole.ASSISTANT.value, final_text, user_id)
        session_manager.save_assistant_message(session_id, final_text, message_id)
        await sio.emit(
            SocketEvent.MESSAGE_COMPLETE.value,
            {"message": final_text, "session_id": session_id, "message_id": message_id},
            room=session_id,
        )
    elif all_chunks:
        final_text = "".join([chunk for _, chunk in all_chunks])
        message_store.save_message(session_id, MessageRole.ASSISTANT.value, final_text, user_id)
        session_manager.save_assistant_message(session_id, final_text, message_id)
        await sio.emit(
            SocketEvent.MESSAGE_CHUNK.value,
            {"chunk": final_text, "session_id": session_id, "message_id": message_id},
            room=session_id,
        )
        await sio.emit(
            SocketEvent.MESSAGE_COMPLETE.value,
            {"message": final_text, "session_id": session_id, "message_id": message_id},
            room=session_id,
        )
