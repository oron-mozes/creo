#!/usr/bin/env python3
"""FastAPI server exposing the orchestrator agent."""
from __future__ import annotations

import os
import sys
import uuid
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
import socketio

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from google.adk.runners import InMemoryRunner
from google.genai import types
from google.cloud import firestore
from datetime import datetime

# Setup environment variables
def setup_env() -> None:
    """
    Setup environment variables for the application.

    Priority:
    1. GEMINI_API_KEY from runtime env (Cloud Run)
    2. GOOGLE_API_KEY from runtime env (fallback)
    3. .env file (local development only)
    """
    # If GEMINI_API_KEY already set (e.g., from Cloud Run Secret Manager), use it
    if "GEMINI_API_KEY" in os.environ:
        return

    # Try GOOGLE_API_KEY as fallback
    if "GOOGLE_API_KEY" in os.environ:
        os.environ["GEMINI_API_KEY"] = os.environ["GOOGLE_API_KEY"]
        return

    # For local development only: load from .env
    env_path = PROJECT_ROOT / ".env"
    if env_path.exists():
        with open(env_path, "r") as env_file:
            for line in env_file:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip()

                # Set GOOGLE_API_KEY as GEMINI_API_KEY
                if key == "GOOGLE_API_KEY" and "GEMINI_API_KEY" not in os.environ:
                    os.environ["GEMINI_API_KEY"] = value

                os.environ.setdefault(key, value)

setup_env()

# Verify required environment variables
required_vars = ["GEMINI_API_KEY", "PINECONE_API_KEY"]
missing_vars = [var for var in required_vars if not os.environ.get(var)]
if missing_vars:
    raise EnvironmentError(
        f"Missing required environment variables: {', '.join(missing_vars)}\n"
        f"For Cloud Run: Ensure secrets are configured in Secret Manager\n"
        f"For local dev: Add to .env file"
    )

# Initialize Firestore (use emulator or mock for local dev)
try:
    # Check if running in Cloud Run (production)
    if os.environ.get('K_SERVICE'):
        db = firestore.Client()
    # Check for Firestore emulator
    elif os.environ.get('FIRESTORE_EMULATOR_HOST'):
        db = firestore.Client()
    # Local development without Firestore - use in-memory storage
    else:
        print("WARNING: Firestore not configured. Using in-memory storage for development.")
        print("To use Firestore locally, set FIRESTORE_EMULATOR_HOST or run with Cloud credentials.")
        db = None
except Exception as e:
    print(f"WARNING: Firestore initialization failed: {e}")
    print("Using in-memory storage for development.")
    db = None

# Import AgentName enum for agent identification
from agents.utils import AgentName

# Import orchestrator agent (handle hyphenated directory name)
import importlib.util
agent_path = PROJECT_ROOT / "agents" / "orchestrator-agent" / "agent.py"
spec = importlib.util.spec_from_file_location("orchestrator_agent", agent_path)
orchestrator_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(orchestrator_module)
root_agent = orchestrator_module.root_agent

# Initialize Socket.IO
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins='*',
    logger=True,
    engineio_logger=True
)

# Initialize FastAPI app
app = FastAPI(
    title="Creo Agent API",
    description="API for interacting with the orchestrator agent and its sub-agents",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files directory
static_dir = PROJECT_ROOT / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Combine FastAPI and Socket.IO
socket_app = socketio.ASGIApp(sio, app)

# Request/Response models
class ChatRequest(BaseModel):
    message: str
    user_id: Optional[str] = "default_user"
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str
    user_id: str

class CreateSessionRequest(BaseModel):
    message: str
    user_id: Optional[str] = None

class CreateSessionResponse(BaseModel):
    session_id: str
    user_id: str

class GetMessagesResponse(BaseModel):
    messages: list
    session_id: str

# In-memory storage (for local dev and active runners)
active_runners = {}
in_memory_messages = {}  # session_id -> list of messages

# Firestore message storage functions
def save_message_to_firestore(session_id: str, role: str, content: str, user_id: str = None):
    """Save a message to Firestore or in-memory storage."""
    if db is not None:
        # Use Firestore
        message_ref = db.collection('sessions').document(session_id).collection('messages').document()
        message_data = {
            'role': role,
            'content': content,
            'timestamp': firestore.SERVER_TIMESTAMP,
            'user_id': user_id
        }
        message_ref.set(message_data)
        return message_ref.id
    else:
        # Use in-memory storage for local development
        if session_id not in in_memory_messages:
            in_memory_messages[session_id] = []

        message_data = {
            'id': str(uuid.uuid4()),
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat(),  # Convert to ISO format string for JSON serialization
            'user_id': user_id
        }
        in_memory_messages[session_id].append(message_data)
        return message_data['id']

def get_session_messages(session_id: str) -> list:
    """Get all messages for a session from Firestore or in-memory storage."""
    if db is not None:
        # Use Firestore
        messages_ref = db.collection('sessions').document(session_id).collection('messages')
        messages = messages_ref.order_by('timestamp').stream()

        result = []
        for msg in messages:
            msg_data = msg.to_dict()
            timestamp = msg_data.get('timestamp')
            # Convert Firestore DatetimeWithNanoseconds to ISO format string for JSON serialization
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

def search_conversation_history(session_id: str, query: str = None, limit: int = 10) -> list:
    """
    Search conversation history for RAG.
    This function can be used as a tool by the orchestrator agent.
    """
    messages = get_session_messages(session_id)

    # If query provided, you could implement semantic search here
    # For now, just return recent messages
    return messages[-limit:] if len(messages) > limit else messages

def get_or_create_runner(user_id: str) -> InMemoryRunner:
    """Get or create a runner for the given user."""
    if user_id not in active_runners:
        active_runners[user_id] = InMemoryRunner(agent=root_agent)
    return active_runners[user_id]

def ensure_session(runner: InMemoryRunner, user_id: str, session_id: str) -> None:
    """Create a session if it doesn't already exist."""
    session_service = runner.session_service
    if hasattr(session_service, "get_session_sync"):
        existing = session_service.get_session_sync(
            app_name=runner.app_name, user_id=user_id, session_id=session_id
        )
    else:
        existing = None
    if existing:
        return
    if hasattr(session_service, "create_session_sync"):
        session_service.create_session_sync(
            app_name=runner.app_name, user_id=user_id, session_id=session_id
        )

def content_to_text(content: types.Content | None) -> str:
    """Extract text from Content object."""
    if not content or not content.parts:
        return ""
    texts = []
    for part in content.parts:
        if getattr(part, "text", None):
            texts.append(part.text)
    return "\n".join(texts).strip()

@app.get("/")
def read_root():
    """Serve the homepage."""
    return FileResponse("static/index.html")

@app.get("/chat/{session_id}")
def chat_page(session_id: str):
    """Serve the chat page with session ID."""
    return FileResponse("static/chat.html")

@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "agent": "orchestrator"}

@app.post("/api/sessions", response_model=CreateSessionResponse)
def create_session(request: CreateSessionRequest):
    """
    Create a new chat session with an initial message.
    Returns session_id to redirect user to chat page.
    """
    session_id = f"session_{uuid.uuid4().hex}"
    user_id = request.user_id or f"user_{uuid.uuid4().hex[:8]}"

    print(f"[CREATE_SESSION] session_id={session_id}, user_id={user_id}, message='{request.message[:50]}...'")

    # Store the initial message in Firestore
    save_message_to_firestore(session_id, "user", request.message, user_id)

    print(f"[CREATE_SESSION] Message stored successfully for session {session_id}")

    return CreateSessionResponse(session_id=session_id, user_id=user_id)

@app.get("/api/sessions/{session_id}/messages", response_model=GetMessagesResponse)
def get_messages(session_id: str):
    """
    Get all messages for a session from Firestore.
    Used when loading the chat page to show existing messages.
    """
    print(f"[GET_MESSAGES] Fetching messages for session {session_id}")
    messages = get_session_messages(session_id)
    print(f"[GET_MESSAGES] Found {len(messages)} messages for session {session_id}")
    return GetMessagesResponse(messages=messages, session_id=session_id)

@app.post("/api/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    """
    Send a message to the orchestrator agent.

    The orchestrator will analyze your request and route it to the appropriate sub-agent:
    - creator_finder_agent: Find influencers/creators
    - campaing_brief_agent: Create campaign briefs
    - outreach_message_agent: Generate outreach messages
    - campaign_builder_agent: Build complete campaign strategies
    """
    try:
        user_id = request.user_id
        session_id = request.session_id or f"session_{uuid.uuid4().hex}"

        # Get or create runner
        runner = get_or_create_runner(user_id)
        ensure_session(runner, user_id, session_id)

        # Create message
        new_message = types.Content(
            role="user",
            parts=[types.Part(text=request.message)],
        )

        # Run agent and collect response
        final_response = None
        all_responses = []

        for event in runner.run(
            user_id=user_id,
            session_id=session_id,
            new_message=new_message,
        ):
            # Log which agent is being triggered
            if event.author:
                print(f"[AGENT_TRIGGERED] Agent: {event.author} | Session: {session_id}")

            # Collect all text responses
            candidate = content_to_text(event.content)
            if candidate:
                all_responses.append(candidate)

            # Track final response
            if event.author == root_agent.name and event.is_final_response():
                if candidate:
                    final_response = candidate

        # Return best available response
        response_text = final_response or "\n".join(all_responses) or "No response generated"

        return ChatResponse(
            response=response_text,
            session_id=session_id,
            user_id=user_id
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/session/{user_id}")
def clear_session(user_id: str):
    """Clear the session for a specific user."""
    if user_id in active_runners:
        del active_runners[user_id]
        return {"status": "success", "message": f"Session cleared for user: {user_id}"}
    return {"status": "not_found", "message": f"No session found for user: {user_id}"}

# Socket.IO Event Handlers
@sio.event
async def connect(sid, environ):
    """Handle client connection."""
    print(f"Client connected: {sid}")

@sio.event
async def disconnect(sid):
    """Handle client disconnection."""
    print(f"Client disconnected: {sid}")

@sio.event
async def join_session(sid, data):
    """
    Join a specific session room and process initial message if it exists.
    This will stream the agent's response to the initial message.
    """
    session_id = data.get('session_id')
    user_id = data.get('user_id', 'default_user')

    print(f"[JOIN_SESSION] Client {sid} requesting to join session {session_id} (user: {user_id})")

    if not session_id:
        print(f"[JOIN_SESSION] ERROR: Missing session_id")
        await sio.emit('error', {'error': 'Missing session_id'}, room=sid)
        return

    # Join the session room
    await sio.enter_room(sid, session_id)
    print(f"[JOIN_SESSION] Client {sid} successfully joined session {session_id}")

    # Send chat history first from Firestore
    messages = get_session_messages(session_id)
    print(f"[JOIN_SESSION] Sending {len(messages)} messages from chat history to client {sid}")
    await sio.emit('chat_history', {
        'messages': messages,
        'session_id': session_id
    }, room=sid)

    # If there's an initial user message and no assistant response yet, process it
    if messages and messages[-1]['role'] == 'user':
        initial_message = messages[-1]['content']
        print(f"[JOIN_SESSION] Last message is from user, processing initial message: '{initial_message[:50]}...'")

        try:
            # Get or create runner
            runner = get_or_create_runner(user_id)
            ensure_session(runner, user_id, session_id)

            # Create message for agent
            new_message = types.Content(
                role="user",
                parts=[types.Part(text=initial_message)],
            )

            # Emit thinking status
            print(f"[JOIN_SESSION] Emitting agent_thinking status")
            await sio.emit('agent_thinking', {'session_id': session_id}, room=session_id)

            # Stream agent responses
            response_chunks = []
            all_chunks = []  # Collect all chunks as fallback
            message_id = str(uuid.uuid4())  # Unique ID for this response
            print(f"[JOIN_SESSION] Starting agent processing")

            got_final_response = False

            for event in runner.run(
                user_id=user_id,
                session_id=session_id,
                new_message=new_message,
            ):
                # Log which agent is being triggered
                if event.author:
                    print(f"[AGENT_TRIGGERED] Agent: {event.author} | Session: {session_id} | is_final: {event.is_final_response()}")

                chunk = content_to_text(event.content)

                # Collect ALL chunks for fallback
                if chunk:
                    all_chunks.append((event.author, chunk))

                # Only emit chunks from frontdesk_agent (the final agent that formats for users)
                # This prevents intermediate agent responses from being sent to the UI
                if chunk and event.author == AgentName.FRONTDESK_AGENT.value:
                    response_chunks.append(chunk)
                    print(f"[JOIN_SESSION] Streaming chunk from frontdesk: '{chunk[:50]}...'")
                    # Emit chunk to client with message ID
                    await sio.emit('message_chunk', {
                        'chunk': chunk,
                        'session_id': session_id,
                        'message_id': message_id
                    }, room=session_id)
                elif chunk:
                    print(f"[JOIN_SESSION] Received chunk from {event.author} (not streaming to client)")

                # Check if final response from root_agent (orchestrator completed the flow)
                if event.author == root_agent.name and event.is_final_response():
                    got_final_response = True
                    final_text = content_to_text(event.content)
                    if final_text:
                        print(f"[JOIN_SESSION] Got final response from root_agent, saving to storage")
                        # Store assistant message in Firestore
                        save_message_to_firestore(session_id, "assistant", final_text, user_id)

                        # Emit final message with message ID
                        print(f"[JOIN_SESSION] Emitting message_complete")
                        await sio.emit('message_complete', {
                            'message': final_text,
                            'session_id': session_id,
                            'message_id': message_id
                        }, room=session_id)
                        break

            # Fallback: If orchestrator didn't complete properly, save what we got
            if not got_final_response:
                if response_chunks:
                    # Prefer frontdesk chunks if available (already streamed to client)
                    final_text = ''.join(response_chunks)
                    print(f"[JOIN_SESSION] WARNING: No final response from root_agent, but saving {len(response_chunks)} frontdesk chunks")
                    save_message_to_firestore(session_id, "assistant", final_text, user_id)
                    await sio.emit('message_complete', {
                        'message': final_text,
                        'session_id': session_id,
                        'message_id': message_id
                    }, room=session_id)
                    # Don't emit chunk again - frontdesk already streamed it
                elif all_chunks:
                    # Fallback to any chunks we collected (from specialized agents)
                    final_text = ''.join([chunk for _, chunk in all_chunks])
                    print(f"[JOIN_SESSION] WARNING: No frontdesk chunks, saving {len(all_chunks)} chunks from other agents")
                    save_message_to_firestore(session_id, "assistant", final_text, user_id)
                    # These weren't streamed, so emit them now
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
    Stream responses back to the client as they're generated.
    """
    try:
        message = data.get('message')
        session_id = data.get('session_id')
        user_id = data.get('user_id', 'default_user')

        print(f"[SEND_MESSAGE] Received message from {sid}: session={session_id}, user={user_id}, message='{message[:50]}...'")

        if not message or not session_id:
            print(f"[SEND_MESSAGE] ERROR: Missing message or session_id")
            await sio.emit('error', {'error': 'Missing message or session_id'}, room=sid)
            return

        # Store user message in Firestore
        print(f"[SEND_MESSAGE] Storing user message in storage")
        save_message_to_firestore(session_id, "user", message, user_id)

        # Get or create runner
        runner = get_or_create_runner(user_id)
        ensure_session(runner, user_id, session_id)

        # Create message for agent
        new_message = types.Content(
            role="user",
            parts=[types.Part(text=message)],
        )

        # Stream agent responses
        response_chunks = []
        all_chunks = []  # Collect all chunks as fallback
        message_id = str(uuid.uuid4())  # Unique ID for this response
        got_final_response = False

        for event in runner.run(
            user_id=user_id,
            session_id=session_id,
            new_message=new_message,
        ):
            # Log which agent is being triggered
            if event.author:
                print(f"[AGENT_TRIGGERED] Agent: {event.author} | Session: {session_id} | is_final: {event.is_final_response()}")

            chunk = content_to_text(event.content)

            # Collect ALL chunks for fallback
            if chunk:
                all_chunks.append((event.author, chunk))

            # Only emit chunks from frontdesk_agent (the final agent that formats for users)
            # This prevents intermediate agent responses from being sent to the UI
            if chunk and event.author == AgentName.FRONTDESK_AGENT.value:
                response_chunks.append(chunk)
                print(f"[SEND_MESSAGE] Streaming chunk from frontdesk: '{chunk[:50]}...'")
                # Emit chunk to client with message ID
                await sio.emit('message_chunk', {
                    'chunk': chunk,
                    'session_id': session_id,
                    'message_id': message_id
                }, room=session_id)
            elif chunk:
                print(f"[SEND_MESSAGE] Received chunk from {event.author} (not streaming to client)")

            # Check if final response from root_agent (orchestrator completed the flow)
            if event.author == root_agent.name and event.is_final_response():
                got_final_response = True
                final_text = content_to_text(event.content)
                if final_text:
                    print(f"[SEND_MESSAGE] Got final response from root_agent, saving to storage")
                    # Store assistant message in Firestore
                    save_message_to_firestore(session_id, "assistant", final_text, user_id)

                    # Emit final message with message ID
                    await sio.emit('message_complete', {
                        'message': final_text,
                        'session_id': session_id,
                        'message_id': message_id
                    }, room=session_id)
                    break

        # Fallback: If orchestrator didn't complete properly, save what we got
        if not got_final_response:
            if response_chunks:
                # Prefer frontdesk chunks if available (already streamed to client)
                final_text = ''.join(response_chunks)
                print(f"[SEND_MESSAGE] WARNING: No final response from root_agent, but saving {len(response_chunks)} frontdesk chunks")
                save_message_to_firestore(session_id, "assistant", final_text, user_id)
                await sio.emit('message_complete', {
                    'message': final_text,
                    'session_id': session_id,
                    'message_id': message_id
                }, room=session_id)
                # Don't emit chunk again - frontdesk already streamed it
            elif all_chunks:
                # Fallback to any chunks we collected (from specialized agents)
                final_text = ''.join([chunk for _, chunk in all_chunks])
                print(f"[SEND_MESSAGE] WARNING: No frontdesk chunks, saving {len(all_chunks)} chunks from other agents")
                save_message_to_firestore(session_id, "assistant", final_text, user_id)
                # These weren't streamed, so emit them now
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(socket_app, host="0.0.0.0", port=8000)
