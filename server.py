#!/usr/bin/env python3
"""FastAPI server exposing the orchestrator agent."""
from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path
from typing import Any, Optional

# Ensure project root is on sys.path before local imports
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def setup_env() -> None:
    """
    Setup environment variables for the application.

    Loads values from .env if present without overwriting explicitly set env vars.
    """
    env_path = PROJECT_ROOT / ".env"
    if env_path.exists():
        with open(env_path, "r") as env_file:
            for line in env_file:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip())


# Load env vars before importing modules that read them (e.g., auth.py)
setup_env()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
import socketio

from auth import router as auth_router, verify_token
from api.chat import build_chat_router
from api.pages import build_pages_router
from api.sessions import build_sessions_router
from api.suggestions import build_suggestions_router
from api.users import build_users_router
from api.creators import build_creators_router
from db import CreatorDB
from services.message_store import MessageStore
from services.user_service import UserService
from session_manager import get_session_manager
from sockets.chat_events import register_chat_socket_handlers
from utils.message_utils import get_business_card


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
    firestore_mod: Optional[Any] = importlib.import_module("google.cloud.firestore")
except Exception:
    firestore_mod = None

if firestore_mod:
    try:
        if os.environ.get('K_SERVICE') or os.environ.get('FIRESTORE_EMULATOR_HOST'):
            db = firestore_mod.Client()
        else:
            print("WARNING: Firestore not configured. Using in-memory storage for development.")
            print("To use Firestore locally, set FIRESTORE_EMULATOR_HOST or run with Cloud credentials.")
            db = None
    except Exception as e:
        print(f"WARNING: Firestore initialization failed: {e}")
        print("Using in-memory storage for development.")
        db = None
else:
    db = None

# Import orchestrator agent
agent_path = PROJECT_ROOT / "agents" / "orchestrator_agent" / "agent.py"
spec = importlib.util.spec_from_file_location("orchestrator_agent", agent_path)
if spec is None or spec.loader is None:
    raise ImportError(f"Could not load orchestrator agent from {agent_path}")
orchestrator_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(orchestrator_module)
root_agent = orchestrator_module.root_agent

# Import suggestions agent
try:
    suggestions_path = PROJECT_ROOT / "agents" / "suggestions_agent" / "agent.py"
    if suggestions_path.exists():
        suggestions_spec = importlib.util.spec_from_file_location("suggestions_agent", suggestions_path)
        if suggestions_spec is None or suggestions_spec.loader is None:
            raise ImportError(f"Could not load suggestions agent from {suggestions_path}")
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

# Initialize services
message_store = MessageStore(db)
user_service = UserService(db)

# Initialize Socket.IO
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins='*',
    logger=True,
    engineio_logger=True
)

# Register socket handlers
register_chat_socket_handlers(
    sio=sio,
    session_manager=session_manager,
    message_store=message_store,
    verify_token=verify_token,
    get_business_card=get_business_card,
    root_agent=root_agent
)

# Initialize FastAPI app
app = FastAPI(
    title="Creo Agent API",
    description="API for interacting with the orchestrator agent and its sub-agents",
    version="1.0.0"
)

# Session middleware required for OAuth state handling
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SESSION_SECRET_KEY", "development-session-secret"),
    same_site="lax",
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
    assets_dir = build_dir / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

# Include domain routers
app.include_router(build_pages_router(PROJECT_ROOT))
app.include_router(build_sessions_router(message_store, user_service))
app.include_router(build_suggestions_router(suggestions_agent, message_store, user_service))
app.include_router(build_chat_router(session_manager, root_agent))
app.include_router(build_users_router(db, message_store, user_service))
app.include_router(build_creators_router(CreatorDB()))

# Combine FastAPI and Socket.IO
socket_app = socketio.ASGIApp(sio, app)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(socket_app, host="0.0.0.0", port=8000)
