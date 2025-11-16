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
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from google.adk.runners import InMemoryRunner
from google.genai import types

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

# Import orchestrator agent (handle hyphenated directory name)
import importlib.util
agent_path = PROJECT_ROOT / "agents" / "orchestrator-agent" / "agent.py"
spec = importlib.util.spec_from_file_location("orchestrator_agent", agent_path)
orchestrator_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(orchestrator_module)
root_agent = orchestrator_module.root_agent

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

# Request/Response models
class ChatRequest(BaseModel):
    message: str
    user_id: Optional[str] = "default_user"
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str
    user_id: str

# In-memory session storage (for demo purposes)
# In production, you'd use a proper session store
active_runners = {}

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

@app.get("/", response_class=HTMLResponse)
def read_root():
    """Root endpoint with API information."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Creo Agent API</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
            h1 { color: #333; }
            .endpoint { background: #f4f4f4; padding: 10px; margin: 10px 0; border-radius: 5px; }
            code { background: #e0e0e0; padding: 2px 6px; border-radius: 3px; }
        </style>
    </head>
    <body>
        <h1>🤖 Creo Agent API</h1>
        <p>Welcome to the Creo Agent API - AI-powered influencer marketing automation</p>

        <h2>API Endpoints</h2>
        <div class="endpoint">
            <strong>POST</strong> <code>/api/chat</code> - Chat with the orchestrator agent
        </div>
        <div class="endpoint">
            <strong>GET</strong> <code>/health</code> - Health check
        </div>
        <div class="endpoint">
            <strong>GET</strong> <code>/docs</code> - Interactive API documentation (Swagger)
        </div>
        <div class="endpoint">
            <strong>DELETE</strong> <code>/api/session/{user_id}</code> - Clear user session
        </div>

        <p><a href="/docs">→ View Interactive API Documentation</a></p>
    </body>
    </html>
    """

@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "agent": "orchestrator"}

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
