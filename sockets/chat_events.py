from __future__ import annotations

import uuid
from typing import Any, Callable

from agents.utils import AgentName
from services.content import content_to_text


def register_chat_socket_handlers(
    sio,
    session_manager,
    message_store,
    verify_token: Callable[[str], Any],
    get_business_card: Callable[[str], Any],
    root_agent
):
    """Register Socket.IO chat event handlers."""

    @sio.event
    async def connect(sid, environ):
        print(f"Client connected: {sid}")

    @sio.event
    async def disconnect(sid):
        print(f"Client disconnected: {sid}")

    @sio.event
    async def join_session(sid, data):
        """
        Join a specific session room and process initial message if it exists.
        Streams the agent's response to the initial message.
        """
        session_id = data.get('session_id')
        token = data.get('token')
        anon_user_id = data.get('user_id')

        user_id = None
        user_profile = None
        if token:
            payload = verify_token(token)
            if payload:
                user_id = payload.get('sub')
                user_profile = {'name': payload.get('name')}
                print(f"[JOIN_SESSION] Authenticated user: {user_id}")
            else:
                print(f"[JOIN_SESSION] WARNING: Invalid token provided, treating as anonymous")

        if not user_id:
            user_id = anon_user_id or f"anon_{sid[:12]}"
            print(f"[JOIN_SESSION] Anonymous user: {user_id}")

        print(f"[JOIN_SESSION] Client {sid} requesting to join session {session_id} (user: {user_id})")

        if not session_id:
            print(f"[JOIN_SESSION] ERROR: Missing session_id")
            await sio.emit('error', {'error': 'Missing session_id'}, room=sid)
            return

        await sio.enter_room(sid, session_id)
        print(f"[JOIN_SESSION] Client {sid} successfully joined session {session_id}")

        print(f"[BUSINESS_CARD] Loading business card for user: {user_id}")
        business_card = get_business_card(user_id)

        if business_card:
            print(f"[BUSINESS_CARD] ✓ Business card found in storage")
            session_manager.load_business_card_into_session(session_id, business_card)
        else:
            print(f"[BUSINESS_CARD] ℹ No business card found for user: {user_id}")
            session_manager.load_business_card_into_session(session_id, None)

        messages = message_store.get_session_messages(session_id)
        print(f"[JOIN_SESSION] Sending {len(messages)} messages from chat history to client {sid}")
        await sio.emit('chat_history', {
            'messages': messages,
            'session_id': session_id
        }, room=sid)

        if messages and messages[-1]['role'] == 'user':
            initial_message = messages[-1]['content']
            print(f"[JOIN_SESSION] Last message is from user, processing initial message: '{initial_message[:50]}...'")

            try:
                await sio.emit('agent_thinking', {'session_id': session_id}, room=sid)
                print(f"[JOIN_SESSION] agent_thinking emitted, starting agent run")

                response_chunks = []
                all_chunks = []
                message_id = str(uuid.uuid4())
                print(f"[JOIN_SESSION] Starting agent processing")

                got_final_response = False
                session_memory = session_manager.get_session_memory(session_id)
                if session_memory:
                    workflow_stage = session_memory.get_workflow_stage()
                    has_business_card = session_memory.has_business_card()
                    print(f"[SESSION_STATE] Session: {session_id} | Stage: {workflow_stage.value if workflow_stage else 'None'} | Business Card: {'Yes' if has_business_card else 'No'}")

                for event in session_manager.run_agent(
                    user_id=user_id,
                    session_id=session_id,
                    message=initial_message,
                    user_profile=user_profile
                ):
                    if event.author:
                        agent_name = event.author
                        is_final = event.is_final_response()
                        print(f"[AGENT_TRANSITION] → {agent_name} | Session: {session_id} | is_final: {is_final}")

                        if session_memory and is_final:
                            new_stage = session_memory.get_workflow_stage()
                            print(f"[WORKFLOW_STATE] After {agent_name}: stage={new_stage.value if new_stage else 'None'}")

                    chunk = content_to_text(event.content)

                    if chunk:
                        all_chunks.append((event.author, chunk))

                    if chunk and event.author == AgentName.FRONTDESK_AGENT.value:
                        response_chunks.append(chunk)
                        print(f"[JOIN_SESSION] Streaming chunk from frontdesk: '{chunk[:50]}...'")
                        await sio.emit('message_chunk', {
                            'chunk': chunk,
                            'session_id': session_id,
                            'message_id': message_id
                        }, room=session_id)
                    elif chunk:
                        print(f"[JOIN_SESSION] Received chunk from {event.author} (not streaming to client)")

                    if event.author == root_agent.name and event.is_final_response():
                        got_final_response = True
                        final_text = content_to_text(event.content)
                        if final_text:
                            print(f"[JOIN_SESSION] Got final response from root_agent ('{root_agent.name}'), saving to storage")
                            print(f"[JOIN_SESSION] Final text preview: {final_text[:200]}...")

                            session_memory_local = session_manager.get_session_memory(session_id)
                            business_card_data = None
                            if session_memory_local:
                                bc = session_memory_local.get_business_card()
                                if bc:
                                    business_card_data = bc

                            message_store.save_message(session_id, "assistant", final_text, user_id)
                            session_manager.save_assistant_message(session_id, final_text, message_id)

                            await sio.emit('message_complete', {
                                'message': final_text,
                                'session_id': session_id,
                                'message_id': message_id,
                                'business_card': business_card_data
                            }, room=session_id)
                            break

                if not got_final_response:
                    if response_chunks:
                        final_text = ''.join(response_chunks)
                        print(f"[JOIN_SESSION] WARNING: No final response from root_agent, but saving {len(response_chunks)} frontdesk chunks")
                        message_store.save_message(session_id, "assistant", final_text, user_id)
                        session_manager.save_assistant_message(session_id, final_text, message_id)
                        await sio.emit('message_complete', {
                            'message': final_text,
                            'session_id': session_id,
                            'message_id': message_id
                        }, room=session_id)
                    elif all_chunks:
                        final_text = ''.join([chunk for _, chunk in all_chunks])
                        print(f"[JOIN_SESSION] WARNING: No frontdesk chunks, saving {len(all_chunks)} chunks from other agents")
                        message_store.save_message(session_id, "assistant", final_text, user_id)
                        session_manager.save_assistant_message(session_id, final_text, message_id)
                        await sio.emit('message_chunk', {
                            'chunk': final_text,
                            'session_id': session_id,
                            'message_id': message_id
                        }, room=session_id)
                        await sio.emit('message_complete', {
                            'message': final_text,
                            'session_id': session_id,
                            'message_id': message_id
                        }, room=session_id)
                    else:
                        print(f"[JOIN_SESSION] ERROR: No response chunks received, showing service error message")
                        error_message = (
                            "⚠️ Our AI service is experiencing technical difficulties right now.\n\n"
                            "This could be due to high traffic on Google's servers.\n\n"
                            "Please try again in a few minutes, or contact support if this persists.\n\n"
                            "We apologize for the inconvenience!"
                        )
                        await sio.emit('message_complete', {
                            'message': error_message,
                            'session_id': session_id,
                            'message_id': message_id,
                            'is_error': True
                        }, room=session_id)

                print(f"[JOIN_SESSION] Initial message processing complete")

            except Exception as e:
                print(f"[JOIN_SESSION] ERROR processing initial message: {str(e)}")
                await sio.emit('error', {'error': str(e)}, room=sid)
        else:
            print(f"[JOIN_SESSION] No initial message to process (messages empty or last message is from assistant)")

    @sio.event
    async def send_message(sid, data):
        """
        Handle incoming message from client via Socket.IO.
        Streams responses back to the client as they're generated.
        """
        try:
            message = data.get('message')
            session_id = data.get('session_id')
            token = data.get('token')
            anon_user_id = data.get('user_id')

            user_id = None
            user_profile = None
            if token:
                payload = verify_token(token)
                if payload:
                    user_id = payload.get('sub')
                    user_profile = {'name': payload.get('name')}
                    print(f"[SEND_MESSAGE] Authenticated user: {user_id}")
                else:
                    print(f"[SEND_MESSAGE] WARNING: Invalid token provided, treating as anonymous")

            if not user_id:
                user_id = anon_user_id or f"anon_{sid[:12]}"
                print(f"[SEND_MESSAGE] Anonymous user: {user_id}")

            print(f"[SEND_MESSAGE] Received message from {sid}: session={session_id}, user={user_id}, message='{(message or '')[:50]}...'")

            if not message or not session_id:
                print(f"[SEND_MESSAGE] ERROR: Missing message or session_id")
                await sio.emit('error', {'error': 'Missing message or session_id'}, room=sid)
                return

            print(f"[SEND_MESSAGE] Storing user message in storage")
            message_store.save_message(session_id, "user", message, user_id)

            await sio.emit('agent_thinking', {'session_id': session_id}, room=session_id)

            response_chunks = []
            all_chunks = []
            message_id = str(uuid.uuid4())
            got_final_response = False

            session_memory = session_manager.get_session_memory(session_id)
            if session_memory:
                workflow_stage = session_memory.get_workflow_stage()
                has_business_card = session_memory.has_business_card()
                print(f"[SESSION_STATE] Session: {session_id} | Stage: {workflow_stage.value if workflow_stage else 'None'} | Business Card: {'Yes' if has_business_card else 'No'}")

            for event in session_manager.run_agent(
                user_id=user_id,
                session_id=session_id,
                message=message,
                user_profile=user_profile
            ):
                if event.author:
                    agent_name = event.author
                    is_final = event.is_final_response()
                    print(f"[AGENT_TRANSITION] → {agent_name} | Session: {session_id} | is_final: {is_final}")

                    if session_memory and is_final:
                        new_stage = session_memory.get_workflow_stage()
                        print(f"[WORKFLOW_STATE] After {agent_name}: stage={new_stage.value if new_stage else 'None'}")

                chunk = content_to_text(event.content)

                if chunk:
                    all_chunks.append((event.author, chunk))

                if chunk and event.author == AgentName.FRONTDESK_AGENT.value:
                    response_chunks.append(chunk)
                    print(f"[SEND_MESSAGE] Streaming chunk from frontdesk: '{chunk[:50]}...'")
                    await sio.emit('message_chunk', {
                        'chunk': chunk,
                        'session_id': session_id,
                        'message_id': message_id
                    }, room=session_id)
                elif chunk:
                    print(f"[SEND_MESSAGE] Received chunk from {event.author} (not streaming to client)")

                if event.author == root_agent.name and event.is_final_response():
                    got_final_response = True
                    final_text = content_to_text(event.content)
                    print(f"[SEND_MESSAGE] DEBUG: Final response from root_agent")
                    print(f"[SEND_MESSAGE] DEBUG: final_text = '{final_text}'")
                    if final_text:
                        print(f"[SEND_MESSAGE] Got final response from root_agent, saving to storage")
                        print(f"[SEND_MESSAGE] Final text preview: {final_text[:200]}...")

                        session_memory_local = session_manager.get_session_memory(session_id)
                        business_card_data = None
                        if session_memory_local:
                            bc = session_memory_local.get_business_card()
                            if bc:
                                business_card_data = bc

                        message_store.save_message(session_id, "assistant", final_text, user_id)
                        session_manager.save_assistant_message(session_id, final_text, message_id)

                        await sio.emit('message_complete', {
                            'message': final_text,
                            'session_id': session_id,
                            'message_id': message_id,
                            'business_card': business_card_data
                        }, room=session_id)
                        break

            if not got_final_response:
                if response_chunks:
                    final_text = ''.join(response_chunks)
                    print(f"[SEND_MESSAGE] WARNING: No final response from root_agent, but saving {len(response_chunks)} frontdesk chunks")
                    message_store.save_message(session_id, "assistant", final_text, user_id)
                    session_manager.save_assistant_message(session_id, final_text, message_id)
                    await sio.emit('message_complete', {
                        'message': final_text,
                        'session_id': session_id,
                        'message_id': message_id
                    }, room=session_id)
                elif all_chunks:
                    final_text = ''.join([chunk for _, chunk in all_chunks])
                    print(f"[SEND_MESSAGE] WARNING: No frontdesk chunks, saving {len(all_chunks)} chunks from other agents")
                    message_store.save_message(session_id, "assistant", final_text, user_id)
                    session_manager.save_assistant_message(session_id, final_text, message_id)
                    await sio.emit('message_chunk', {
                        'chunk': final_text,
                        'session_id': session_id,
                        'message_id': message_id
                    }, room=session_id)
                    await sio.emit('message_complete', {
                        'message': final_text,
                        'session_id': session_id,
                        'message_id': message_id
                    }, room=session_id)

        except Exception as e:
            print(f"Error in send_message: {str(e)}")
            await sio.emit('error', {'error': str(e)}, room=sid)
