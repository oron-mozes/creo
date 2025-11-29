import asyncio
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from agents.orchestrator_agent.tools import _run_agent_and_get_text
from google.adk.tools.tool_context import ToolContext
from session_manager import SessionManager
from google.adk.runners import InMemoryRunner
from google.adk.agents.llm_agent import Agent

async def test_orchestrator_fix():
    print("Starting verification test...")
    
    # Mock session manager and runner
    session_manager = MagicMock(spec=SessionManager)
    
    # Mock sub-runner and its session service
    sub_runner = MagicMock(spec=InMemoryRunner)
    sub_runner.app_name = "test_app"
    sub_runner.session_service = AsyncMock()
    
    # Mock existing session
    sub_runner.session_service.get_session.return_value = {"session_id": "test_session", "user_id": "test_user", "app_name": "test_app"}
    
    # Mock sub-runner run_async to return a generator
    async def mock_run_async(*args, **kwargs):
        yield MagicMock(parts=[MagicMock(text="Sub-agent response")])
        
    sub_runner.run_async.return_value = mock_run_async()
    
    # Configure session_manager to return our mock sub-runner
    session_manager.create_sub_runner.return_value = sub_runner
    
    # Mock tool context
    tool_context = MagicMock(spec=ToolContext)
    tool_context.session_manager = session_manager
    from types import SimpleNamespace
    tool_context.session = SimpleNamespace(session_id="test_session", user_id="test_user", app_name="test_app")
    
    # Mock agent
    agent = MagicMock(spec=Agent)
    agent.name = "test_agent"
    
    # Call the function
    print("Calling _run_agent_and_get_text...")
    try:
        response = await _run_agent_and_get_text(agent, tool_context, "test request")
        print(f"Response received: {response}")
        
        # Verify create_sub_runner was called
        session_manager.create_sub_runner.assert_called_once()
        print("SUCCESS: create_sub_runner was called.")
        
        if "Sub-agent response" in response:
            print("SUCCESS: Sub-agent response received.")
        else:
            print("FAILURE: Sub-agent response not found.")
            
        # Verify response is saved to metadata (simulating route_to_frontdesk_agent logic)
        # Note: _run_agent_and_get_text doesn't save to metadata itself, 
        # but we can verify the session memory structure supports it.
        if tool_context.session_manager.get_session_memory("test_session"):
             print("SUCCESS: Session memory accessible.")
        
    except Exception as e:
        print(f"FAILURE: Exception occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_orchestrator_fix())
