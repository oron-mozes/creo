#!/usr/bin/env python3
"""FastAPI server exposing the orchestrator agent."""
from __future__ import annotations

import os
import sys
import uuid
import json
import re
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
import socketio

# Import authentication
from auth import router as auth_router, get_current_user, get_optional_user, UserInfo, verify_token

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
    1. GOOGLE_API_KEY from runtime env (Cloud Run)
    2. GOOGLE_API_KEY from runtime env (fallback)
    3. .env file (local development only)
    """
    # If GOOGLE_API_KEY already set (e.g., from Cloud Run Secret Manager), use it
    if "GOOGLE_API_KEY" in os.environ:
        return

    # Try GOOGLE_API_KEY as fallback
    if "GOOGLE_API_KEY" in os.environ:
        os.environ["GOOGLE_API_KEY"] = os.environ["GOOGLE_API_KEY"]
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

                # Set GOOGLE_API_KEY as GOOGLE_API_KEY
                if key == "GOOGLE_API_KEY" and "GOOGLE_API_KEY" not in os.environ:
                    os.environ["GOOGLE_API_KEY"] = value

                os.environ.setdefault(key, value)

setup_env()

# Verify required environment variables
required_vars = ["GOOGLE_API_KEY", "PINECONE_API_KEY"]
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

# Import SessionManager for runner and memory management
from session_manager import get_session_manager

# Import orchestrator agent
import importlib.util
agent_path = PROJECT_ROOT / "agents" / "orchestrator_agent" / "agent.py"
spec = importlib.util.spec_from_file_location("orchestrator_agent", agent_path)
orchestrator_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(orchestrator_module)
root_agent = orchestrator_module.root_agent

# Import suggestions agent
try:
    suggestions_path = PROJECT_ROOT / "agents" / "suggestions_agent" / "agent.py"
    if suggestions_path.exists():
        suggestions_spec = importlib.util.spec_from_file_location("suggestions_agent", suggestions_path)
        suggestions_module = importlib.util.module_from_spec(suggestions_spec)
        suggestions_spec.loader.exec_module(suggestions_module)
        suggestions_agent = suggestions_module.suggestions_agent
    else:
        suggestions_agent = None
except Exception as e:
    print(f"[WARNING] Could not load suggestions agent: {e}")
    suggestions_agent = None

# Initialize session manager
session_manager = get_session_manager()
session_manager.set_root_agent(root_agent)

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

# Include authentication router
app.include_router(auth_router)

# Mount static files directory
static_dir = PROJECT_ROOT / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Mount React build directory if it exists (production)
build_dir = PROJECT_ROOT / "build"
if build_dir.exists():
    print(f"[SERVER] Serving React build from {build_dir}")
    # Mount build/assets as /assets for production
    assets_dir = build_dir / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

# Combine FastAPI and Socket.IO
socket_app = socketio.ASGIApp(sio, app)

# Request/Response models
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str

class CreateSessionRequest(BaseModel):
    message: str

class CreateSessionResponse(BaseModel):
    session_id: str
    user_id: str

class GetMessagesResponse(BaseModel):
    messages: list
    session_id: str

class SuggestionsResponse(BaseModel):
    welcome_message: str
    suggestions: list[str]

class SessionInfo(BaseModel):
    id: str
    title: str
    timestamp: str

class GetSessionsResponse(BaseModel):
    sessions: list[SessionInfo]

# In-memory storage (for local dev)
in_memory_messages = {}  # session_id -> list of messages
# Note: Runners are now managed by SessionManager

# Firestore message storage functions
def save_message_to_firestore(session_id: str, role: str, content: str, user_id: str = None):
    """Save a message to Firestore or in-memory storage."""
    if db is not None:
        # Use Firestore - save to both locations:
        # 1. In session subcollection (for get_session_messages)
        # 2. In top-level messages collection (for get_user_sessions query)

        message_data = {
            'role': role,
            'content': content,
            'timestamp': firestore.SERVER_TIMESTAMP,
            'user_id': user_id,
            'session_id': session_id  # Add session_id for top-level collection
        }

        # Save to session subcollection
        message_ref = db.collection('sessions').document(session_id).collection('messages').document()
        message_ref.set(message_data)

        # Also save to top-level messages collection for easy session queries
        db.collection('messages').document(message_ref.id).set(message_data)

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

def get_user_past_sessions(user_id: str, limit: int = 5) -> list:
    """
    Get past sessions for a user with brief summaries.
    
    Args:
        user_id: The user identifier
        limit: Maximum number of sessions to return
        
    Returns:
        List of session summaries with session_id and first message
    """
    if db is not None:
        # Use Firestore
        sessions_ref = db.collection('sessions')
        # Get sessions by querying messages collection
        # For now, we'll get recent sessions from in-memory or return empty
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

# Runner and session management now handled by SessionManager
# See session_manager.py for implementation

# Import business card storage functions from utils
from utils.message_utils import save_business_card, get_business_card

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
    """Serve the unified SPA (React build in production, fallback to static/app.html in dev)."""
    build_index = PROJECT_ROOT / "build" / "index.html"
    if build_index.exists():
        return FileResponse(build_index)
    return FileResponse("static/app.html")

@app.get("/index.html")
def index_page():
    """Redirect index.html to unified SPA."""
    build_index = PROJECT_ROOT / "build" / "index.html"
    if build_index.exists():
        return FileResponse(build_index)
    return FileResponse("static/app.html")

@app.get("/login.html")
def login_page():
    """Serve the login page."""
    return FileResponse("static/login.html")

@app.get("/chat/{session_id}")
def chat_page(session_id: str):
    """Serve the unified SPA for chat sessions."""
    return FileResponse("static/app.html")

@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "agent": "orchestrator"}

class CreateSessionRequestWithUser(BaseModel):
    message: str
    user_id: Optional[str] = None  # For anonymous users
    session_id: Optional[str] = None  # Optional session_id to use existing session

@app.post("/api/sessions", response_model=CreateSessionResponse)
def create_session(
    request: CreateSessionRequestWithUser,
    current_user: Optional[UserInfo] = Depends(get_optional_user)
):
    """
    Create a new chat session with an initial message.
    Returns session_id to redirect user to chat page.

    Works for both authenticated and anonymous users.
    If session_id is provided, uses that instead of generating a new one.
    """
    # Use provided session_id or generate a new one
    session_id = request.session_id or f"session_{uuid.uuid4().hex}"

    # Use authenticated user ID if available, otherwise use provided user_id (anonymous)
    if current_user:
        user_id = current_user.user_id
        print(f"[CREATE_SESSION] Authenticated user: {user_id}")
    else:
        user_id = request.user_id or f"anon_{uuid.uuid4().hex[:12]}"
        print(f"[CREATE_SESSION] Anonymous user: {user_id}")

    print(f"[CREATE_SESSION] session_id={session_id}, user_id={user_id}, message='{request.message[:50]}...'")

    # Save the initial message so it's available when client joins via WebSocket
    save_message_to_firestore(session_id, 'user', request.message, user_id)
    print(f"[CREATE_SESSION] Initial message saved to storage")

    print(f"[CREATE_SESSION] Session created: {session_id}")

    return CreateSessionResponse(session_id=session_id, user_id=user_id)

@app.get("/api/sessions", response_model=GetSessionsResponse)
def get_user_sessions(user_id: str):
    """
    Get all chat sessions for a user.
    Returns list of sessions with id, title, and timestamp.
    """
    print(f"[GET_SESSIONS] Fetching sessions for user {user_id}")

    try:
        sessions = []

        # Query Firestore for all sessions belonging to this user
        if db:
            # Firestore: query messages collection grouped by session_id
            messages_ref = db.collection('messages')
            query = messages_ref.where('user_id', '==', user_id).order_by('timestamp', direction=firestore.Query.DESCENDING).limit(100)
            docs = query.stream()

            # Group messages by session_id to get unique sessions
            session_map = {}
            for doc in docs:
                data = doc.to_dict()
                session_id = data.get('session_id')
                if session_id and session_id not in session_map:
                    # Get first user message as title
                    if data.get('role') == 'user':
                        title = data.get('content', 'New Chat')[:50]
                    else:
                        title = 'New Chat'

                    session_map[session_id] = {
                        'id': session_id,
                        'title': title,
                        'timestamp': data.get('timestamp', datetime.now()).isoformat()
                    }

            # Convert to list and sort by timestamp descending (latest first)
            sessions = sorted(session_map.values(), key=lambda s: s['timestamp'], reverse=True)
        else:
            # In-memory fallback: get from in_memory_messages
            for session_id, msgs in in_memory_messages.items():
                if msgs:
                    # Check if any message belongs to this user
                    user_msgs = [m for m in msgs if m.get('user_id') == user_id]
                    if user_msgs:
                        first_user_msg = next((m for m in msgs if m.get('role') == 'user'), None)
                        title = first_user_msg['content'][:50] if first_user_msg else 'New Chat'
                        timestamp = msgs[0].get('timestamp', datetime.now().isoformat())
                        sessions.append({
                            'id': session_id,
                            'title': title,
                            'timestamp': timestamp
                        })

            # Sort by timestamp descending (latest first)
            sessions = sorted(sessions, key=lambda s: s['timestamp'], reverse=True)

        print(f"[GET_SESSIONS] Found {len(sessions)} sessions for user {user_id}")
        return GetSessionsResponse(sessions=sessions)

    except Exception as e:
        print(f"[GET_SESSIONS] Error: {e}")
        import traceback
        traceback.print_exc()
        return GetSessionsResponse(sessions=[])

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

class SuggestionsRequest(BaseModel):
    user_id: Optional[str] = None


@app.post("/api/suggestions", response_model=SuggestionsResponse)
def get_suggestions(
    request: SuggestionsRequest,
    current_user: Optional[UserInfo] = Depends(get_optional_user)
):
    """
    Get personalized welcome message and campaign suggestions for a user.

    This endpoint:
    1. Retrieves the user's business card (if available)
    2. Gets past session summaries
    3. Calls the suggestions agent to generate personalized content
    4. Returns welcome message and 4 campaign suggestions

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

        # Get business card
        business_card = get_business_card(user_id)
        print(f"[SUGGESTIONS] Business card for user {user_id}: {business_card}")
        
        # Get past sessions
        past_sessions = get_user_past_sessions(user_id, limit=5)
        print(f"[SUGGESTIONS] Past sessions for user {user_id}: {len(past_sessions)}")
        
        # Build context for suggestions agent
        context_parts = []
        
        if business_card:
            context_parts.append(f"Business Card Information:\n{json.dumps(business_card, indent=2)}")
        else:
            context_parts.append("Business Card: None (not collected yet)")
        
        if past_sessions:
            context_parts.append(f"\nPast Sessions ({len(past_sessions)}):")
            for i, session in enumerate(past_sessions, 1):
                context_parts.append(f"{i}. Session {session['session_id'][:8]}... - First message: {session.get('first_message', '')}")
        else:
            context_parts.append("\nPast Sessions: None (new user)")
        
        context = "\n".join(context_parts)
        
        # Run suggestions agent in an isolated temp session (sessionless personalization via prompt)
        temp_session_id = f"temp_suggestions_{uuid.uuid4().hex}"
        runner = InMemoryRunner(agent=suggestions_agent, app_name="agents")
        # Ensure the temp session exists before running the agent to avoid session-not-found errors
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
            """Create the temp session if it doesn't exist (avoid session-not-found)."""
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
            # If the session wasn't found (e.g., mismatch or race), recreate and retry once
            if "Session not found" in str(e):
                print(f"[SUGGESTIONS] Session not found, recreating temp session and retrying: {temp_session_id}")
                _ensure_temp_session()
                response_text = _run_suggestions()
            else:
                raise
        
        print(f"[SUGGESTIONS] Agent response: {response_text[:200]}...")
        
        print(f"[SUGGESTIONS] Agent response: {response_text[:200]}...")
        
        # Parse JSON response
        try:
            # Extract JSON from response (might have markdown code blocks)
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
            else:
                json_str = response_text
            
            suggestions_data = json.loads(json_str)
            
            welcome_message = suggestions_data.get("welcome_message", "Hey! 👋 I'm here to help you connect with amazing influencers. Just tell me what you're looking for, and I'll find the perfect match for your business!")
            suggestions = suggestions_data.get("suggestions", [])
            
            # Ensure exactly 4 suggestions
            if len(suggestions) < 4:
                # Pad with defaults if needed
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
            # Return defaults on parse error
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
        # Return defaults on error
        return SuggestionsResponse(
            welcome_message="Hey! 👋 I'm here to help you connect with amazing influencers. Just tell me what you're looking for, and I'll find the perfect match for your business!",
            suggestions=[
                "I have a local coffee shop",
                "I sell handmade jewelry online",
                "I run a small gym",
                "I own a boutique hotel"
            ]
        )

class ChatRequestWithUser(BaseModel):
    message: str
    session_id: Optional[str] = None
    user_id: Optional[str] = None  # For anonymous users

@app.post("/api/chat", response_model=ChatResponse)
def chat(
    request: ChatRequestWithUser,
    current_user: Optional[UserInfo] = Depends(get_optional_user)
):
    """
    Send a message to the orchestrator agent.

    The orchestrator will analyze your request and route it to the appropriate sub-agent:
    - creator_finder_agent: Find influencers/creators
    - campaign_brief_agent: Create campaign briefs
    - outreach_message_agent: Generate outreach messages (requires authentication)
    - campaign_builder_agent: Build complete campaign strategies

    Works for both authenticated and anonymous users.
    Anonymous users can find influencers but must log in for outreach.
    """
    try:
        # Use authenticated user ID if available, otherwise use provided user_id (anonymous)
        user_profile = None
        if current_user:
            user_id = current_user.user_id
            user_profile = {
                'name': current_user.name
            }
            print(f"[CHAT] Authenticated user: {user_id}")
        else:
            user_id = request.user_id or f"anon_{uuid.uuid4().hex[:12]}"
            print(f"[CHAT] Anonymous user: {user_id}")

        session_id = request.session_id or f"session_{uuid.uuid4().hex}"

        # Run agent and collect response
        final_response = None
        all_responses = []

        # Get session memory for logging
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
            # Log which agent is being triggered with transitions
            if event.author:
                agent_name = event.author
                is_final = event.is_final_response()
                print(f"[AGENT_TRANSITION] → {agent_name} | Session: {session_id} | is_final: {is_final}")

                # Log workflow state after each agent response
                if session_memory and is_final:
                    new_stage = session_memory.get_workflow_stage()
                    print(f"[WORKFLOW_STATE] After {agent_name}: stage={new_stage.value if new_stage else 'None'}")

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

        # Save assistant response to session memory
        session_manager.save_assistant_message(session_id, response_text)

        return ChatResponse(
            response=response_text,
            session_id=session_id
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/session/{user_id}")
def clear_session(user_id: str):
    """Clear all sessions for a specific user."""
    session_manager.clear_user_sessions(user_id)
    return {"status": "success", "message": f"Sessions cleared for user: {user_id}"}

class MigrateUserRequest(BaseModel):
    anonymous_user_id: str

@app.post("/api/users/migrate")
def migrate_anonymous_user(
    request: MigrateUserRequest,
    current_user: UserInfo = Depends(get_current_user)
):
    """
    Migrate anonymous user data to authenticated user.

    This endpoint:
    1. Takes the anonymous user ID
    2. Links all their sessions, business cards, etc. to the authenticated user
    3. Marks the migration as complete

    Requires authentication (user must be logged in to migrate).
    """
    anon_user_id = request.anonymous_user_id
    auth_user_id = current_user.user_id

    print(f"[MIGRATION] Migrating anonymous user {anon_user_id} to authenticated user {auth_user_id}")

    try:
        # In Firestore, we would:
        # 1. Find all sessions/data with anon_user_id
        # 2. Update them to auth_user_id
        # 3. Merge business cards if both exist

        # For now, we'll just log the migration
        # In production, implement actual data migration logic

        if db is not None:
            # TODO: Implement Firestore migration
            # Example:
            # - Update all sessions where user_id = anon_user_id to user_id = auth_user_id
            # - Merge business cards
            # - Update message ownership
            pass

        print(f"[MIGRATION] Successfully migrated {anon_user_id} to {auth_user_id}")

        return {
            "status": "success",
            "message": f"Migrated {anon_user_id} to {auth_user_id}",
            "anonymous_user_id": anon_user_id,
            "authenticated_user_id": auth_user_id
        }

    except Exception as e:
        print(f"[MIGRATION] Error: {e}")
        raise HTTPException(status_code=500, detail=f"Migration failed: {str(e)}")

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

    Works for both authenticated and anonymous users.
    """
    session_id = data.get('session_id')
    token = data.get('token')
    anon_user_id = data.get('user_id')  # For anonymous users

    # Try to authenticate, but allow anonymous
    user_id = None
    user_profile = None
    if token:
        payload = verify_token(token)
        if payload:
            user_id = payload.get('sub')
            user_profile = {
                'name': payload.get('name')
            }
            print(f"[JOIN_SESSION] Authenticated user: {user_id}")
        else:
            print(f"[JOIN_SESSION] WARNING: Invalid token provided, treating as anonymous")

    # If no valid auth, use anonymous user ID
    if not user_id:
        user_id = anon_user_id or f"anon_{sid[:12]}"
        print(f"[JOIN_SESSION] Anonymous user: {user_id}")

    print(f"[JOIN_SESSION] Client {sid} requesting to join session {session_id} (user: {user_id})")

    if not session_id:
        print(f"[JOIN_SESSION] ERROR: Missing session_id")
        await sio.emit('error', {'error': 'Missing session_id'}, room=sid)
        return

    # Join the session room
    await sio.enter_room(sid, session_id)
    print(f"[JOIN_SESSION] Client {sid} successfully joined session {session_id}")

    # Load business card from persistent storage into session memory
    print(f"[BUSINESS_CARD] Loading business card for user: {user_id}")
    business_card = get_business_card(user_id)

    if business_card:
        print(f"[BUSINESS_CARD] ✓ Business card found in storage:")
        print(f"[BUSINESS_CARD]   - Name: {business_card.get('name')}")
        print(f"[BUSINESS_CARD]   - Location: {business_card.get('location')}")
        print(f"[BUSINESS_CARD]   - Service Type: {business_card.get('service_type')}")
        session_manager.load_business_card_into_session(session_id, business_card)
        print(f"[BUSINESS_CARD] ✓ Business card loaded into session {session_id}")
    else:
        print(f"[BUSINESS_CARD] ℹ No business card found for user: {user_id} (new user or onboarding not completed)")
        session_manager.load_business_card_into_session(session_id, None)

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
            # Emit thinking status to the specific client
            print(f"[JOIN_SESSION] Emitting agent_thinking status for session {session_id}")
            await sio.emit('agent_thinking', {'session_id': session_id}, room=sid)
            print(f"[JOIN_SESSION] agent_thinking emitted, starting agent run")

            # Stream agent responses
            response_chunks = []
            all_chunks = []  # Collect all chunks as fallback
            message_id = str(uuid.uuid4())  # Unique ID for this response
            print(f"[JOIN_SESSION] Starting agent processing")

            got_final_response = False

            # Get session memory for logging
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
                # Log which agent is being triggered with transitions
                if event.author:
                    agent_name = event.author
                    is_final = event.is_final_response()
                    print(f"[AGENT_TRANSITION] → {agent_name} | Session: {session_id} | is_final: {is_final}")

                    # Log workflow state after each agent response
                    if session_memory and is_final:
                        new_stage = session_memory.get_workflow_stage()
                        print(f"[WORKFLOW_STATE] After {agent_name}: stage={new_stage.value if new_stage else 'None'}")

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
                if event.is_final_response():
                    print(f"[JOIN_SESSION] Got final response from {event.author}")

                if event.author == root_agent.name and event.is_final_response():
                    got_final_response = True
                    final_text = content_to_text(event.content)
                    if final_text:
                        print(f"[JOIN_SESSION] Got final response from root_agent ('{root_agent.name}'), saving to storage")
                        print(f"[JOIN_SESSION] Final text preview: {final_text[:200]}...")

                        # Business card saving is now handled by the onboarding agent's save_business_card tool
                        # No need to parse or intercept here

                        # Check if business card was saved by the tool (it's in session memory)
                        session_memory = session_manager.get_session_memory(session_id)
                        business_card_data = None
                        if session_memory:
                            bc = session_memory.get_business_card()
                            if bc:
                                business_card_data = bc
                                print(f"[JOIN_SESSION] Business card found in session memory")

                        # Store assistant message in Firestore and session memory
                        save_message_to_firestore(session_id, "assistant", final_text, user_id)
                        session_manager.save_assistant_message(session_id, final_text, message_id)

                        # Emit final message with message ID and business card data
                        print(f"[JOIN_SESSION] Emitting message_complete")
                        await sio.emit('message_complete', {
                            'message': final_text,
                            'session_id': session_id,
                            'message_id': message_id,
                            'business_card': business_card_data
                        }, room=session_id)
                        break

            # Fallback: If orchestrator didn't complete properly, save what we got
            if not got_final_response:
                if response_chunks:
                    # Prefer frontdesk chunks if available (already streamed to client)
                    final_text = ''.join(response_chunks)
                    print(f"[JOIN_SESSION] WARNING: No final response from root_agent, but saving {len(response_chunks)} frontdesk chunks")
                    save_message_to_firestore(session_id, "assistant", final_text, user_id)
                    session_manager.save_assistant_message(session_id, final_text, message_id)
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
                    session_manager.save_assistant_message(session_id, final_text, message_id)
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
                else:
                    # No chunks at all - likely a 503 error or other service failure
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
    Stream responses back to the client as they're generated.

    Works for both authenticated and anonymous users.
    """
    try:
        message = data.get('message')
        session_id = data.get('session_id')
        token = data.get('token')
        anon_user_id = data.get('user_id')  # For anonymous users

        # Try to authenticate, but allow anonymous
        user_id = None
        user_profile = None
        if token:
            payload = verify_token(token)
            if payload:
                user_id = payload.get('sub')
                user_profile = {
                    'name': payload.get('name')
                }
                print(f"[SEND_MESSAGE] Authenticated user: {user_id}")
            else:
                print(f"[SEND_MESSAGE] WARNING: Invalid token provided, treating as anonymous")

        # If no valid auth, use anonymous user ID
        if not user_id:
            user_id = anon_user_id or f"anon_{sid[:12]}"
            print(f"[SEND_MESSAGE] Anonymous user: {user_id}")

        print(f"[SEND_MESSAGE] Received message from {sid}: session={session_id}, user={user_id}, message='{message[:50]}...'")

        if not message or not session_id:
            print(f"[SEND_MESSAGE] ERROR: Missing message or session_id")
            await sio.emit('error', {'error': 'Missing message or session_id'}, room=sid)
            return

        # Note: Business card loading is now handled by the load_business_card tool
        # The onboarding agent will call this tool to check for existing business cards

        # Store user message in Firestore
        print(f"[SEND_MESSAGE] Storing user message in storage")
        save_message_to_firestore(session_id, "user", message, user_id)

        # Emit thinking status
        print(f"[SEND_MESSAGE] Emitting agent_thinking status")
        await sio.emit('agent_thinking', {'session_id': session_id}, room=session_id)

        # Stream agent responses
        response_chunks = []
        all_chunks = []  # Collect all chunks as fallback
        message_id = str(uuid.uuid4())  # Unique ID for this response
        got_final_response = False

        # Get session memory for logging
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
            # Log which agent is being triggered with transitions
            if event.author:
                agent_name = event.author
                is_final = event.is_final_response()
                print(f"[AGENT_TRANSITION] → {agent_name} | Session: {session_id} | is_final: {is_final}")

                # Log workflow state after each agent response
                if session_memory and is_final:
                    new_stage = session_memory.get_workflow_stage()
                    print(f"[WORKFLOW_STATE] After {agent_name}: stage={new_stage.value if new_stage else 'None'}")

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
                print(f"[SEND_MESSAGE] DEBUG: Final response from root_agent")
                print(f"[SEND_MESSAGE] DEBUG: event.content = {event.content}")
                print(f"[SEND_MESSAGE] DEBUG: final_text = '{final_text}'")
                print(f"[SEND_MESSAGE] DEBUG: final_text length = {len(final_text) if final_text else 0}")
                if final_text:
                    print(f"[SEND_MESSAGE] Got final response from root_agent, saving to storage")
                    print(f"[SEND_MESSAGE] Final text preview: {final_text[:200]}...")

                    # Business card saving is now handled by the onboarding agent's save_business_card tool
                    # No need to parse or intercept here

                    # Check if business card was saved by the tool (it's in session memory)
                    session_memory = session_manager.get_session_memory(session_id)
                    business_card_data = None
                    if session_memory:
                        bc = session_memory.get_business_card()
                        if bc:
                            business_card_data = bc
                            print(f"[SEND_MESSAGE] Business card found in session memory")

                    # Store assistant message in Firestore and session memory
                    save_message_to_firestore(session_id, "assistant", final_text, user_id)
                    session_manager.save_assistant_message(session_id, final_text, message_id)

                    # Emit final message with message ID and business card data
                    await sio.emit('message_complete', {
                        'message': final_text,
                        'session_id': session_id,
                        'message_id': message_id,
                        'business_card': business_card_data
                    }, room=session_id)
                    break

        # Fallback: If orchestrator didn't complete properly, save what we got
        if not got_final_response:
            if response_chunks:
                # Prefer frontdesk chunks if available (already streamed to client)
                final_text = ''.join(response_chunks)
                print(f"[SEND_MESSAGE] WARNING: No final response from root_agent, but saving {len(response_chunks)} frontdesk chunks")
                save_message_to_firestore(session_id, "assistant", final_text, user_id)
                session_manager.save_assistant_message(session_id, final_text, message_id)
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
                session_manager.save_assistant_message(session_id, final_text, message_id)
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
