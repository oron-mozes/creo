import asyncio
from unittest.mock import MagicMock, patch
from types import SimpleNamespace
from agents.outreach_message_agent.tools_auth import require_auth_for_outreach_tool
from sockets.handlers.run_agent import _handle_root_final
from session_manager import SessionManager, SessionMemory
from workflow_enums import WorkflowStage

async def test_auth_flow():
    print("Starting auth flow verification...")

    # 1. Setup mocks
    session_id = "test_session"
    user_id = "test_user"
    
    session_manager = MagicMock(spec=SessionManager)
    session_memory = SessionMemory(session_id, user_id)
    session_manager.get_session_memory.return_value = session_memory
    
    # Mock context for tool
    with patch("agents.outreach_message_agent.tools_auth.get_context") as mock_get_context:
        mock_get_context.return_value = {
            "session_manager": session_manager,
            "session_id": session_id,
            "user_id": user_id
        }
        
        # 2. Test Tool Execution (Unauthenticated)
        print("\nTesting require_auth_for_outreach_tool (Unauthenticated)...")
        with patch("agents.outreach_message_agent.tools_auth.is_authenticated_user", return_value=False):
            result = require_auth_for_outreach_tool()
            print(f"Tool result: {result}")
            
            # Verify metadata flag is set
            metadata = session_memory.get_shared_context().get("metadata", {})
            if metadata.get("auth_required_triggered"):
                print("SUCCESS: auth_required_triggered flag set in metadata.")
            else:
                print("FAILURE: auth_required_triggered flag NOT set.")

    # 3. Test Socket Handler Logic
    print("\nTesting _handle_root_final logic...")
    
    sio = MagicMock()
    message_store = MagicMock()
    root_agent = MagicMock()
    root_agent.name = "root_agent"
    
    # Ensure flag is set (simulating tool run)
    session_memory.get_shared_context().setdefault("metadata", {})["auth_required_triggered"] = True
    
    _handle_root_final(
        author="root_agent",
        is_final_event=True,
        final_text="Please login",
        session_manager=session_manager,
        session_id=session_id,
        user_id=user_id,
        is_authenticated=False,
        message_store=message_store,
        message_id="msg_123",
        sio=sio,
        root_agent=root_agent
    )
    
    # Verify emit call
    sio.start_background_task.assert_called()
    call_args = sio.start_background_task.call_args
    emit_args = call_args[0] # (emit_func, event, data, room=...)
    event_data = emit_args[2]
    
    print(f"Emitted event data: {event_data}")
    
    if event_data.get("auth_required") is True:
        print("SUCCESS: auth_required=True in emitted event.")
    else:
        print("FAILURE: auth_required=True NOT found in emitted event.")
        
    # Verify flag is cleared
    metadata = session_memory.get_shared_context().get("metadata", {})
    if not metadata.get("auth_required_triggered"):
        print("SUCCESS: auth_required_triggered flag cleared.")
    else:
        print("FAILURE: auth_required_triggered flag NOT cleared.")

if __name__ == "__main__":
    asyncio.run(test_auth_flow())
