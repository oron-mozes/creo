"""Tools for the onboarding agent to collect and save business information."""
from typing import Optional, Dict, Any
from google.adk.tools import FunctionTool
import threading
from agents.onboarding_agent.models import BusinessCard

# Global session context storage with thread safety
# Note: ADK executes tools in different threads, so we use a global dict with a lock
# The key is the session_id, allowing multiple concurrent sessions
_session_contexts: Dict[str, Dict[str, Any]] = {}
_context_lock = threading.Lock()
_current_session_id: str = None


def set_session_context(session_manager, session_id: str):
    """Set the session context for tools to access user_id.

    This is called by the server before running the agent.
    Stores context globally so tools executing in different threads can access it.
    """
    global _current_session_id
    with _context_lock:
        _session_contexts[session_id] = {
            'session_manager': session_manager,
            'session_id': session_id
        }
        _current_session_id = session_id


def save_business_card_tool(
    name: str,
    location: str,
    service_type: str,
    website: Optional[str] = None,
    social_links: Optional[str] = None
) -> str:
    """Save business card information to the database.

    This tool saves the collected business information after user confirmation.
    Call this tool when the user has confirmed all their business details.

    Args:
        name: Business name (required)
        location: Business location - city, state, country, or full address (required)
        service_type: Type of business/service offered (required)
        website: Business website URL (optional)
        social_links: Social media profiles - comma-separated URLs (optional)

    Returns:
        JSON string with success status and message
    """
    import json

    # Get session context from global storage (thread-safe)
    # Use the most recent session_id
    global _current_session_id
    with _context_lock:
        if not _current_session_id or _current_session_id not in _session_contexts:
            print("[TOOL ERROR] Session context not set - cannot save business card")
            print(f"[TOOL ERROR] Current session: {_current_session_id}, Available sessions: {list(_session_contexts.keys())}")
            return json.dumps({
                "success": False,
                "error": "Session context not available"
            })

        context = _session_contexts[_current_session_id]
        session_manager = context['session_manager']
        session_id = context['session_id']

    # Get user_id from session context
    if not session_manager or not session_id:
        print("[TOOL ERROR] Session context incomplete - cannot save business card")
        return json.dumps({
            "success": False,
            "error": "Session context incomplete"
        })

    session_memory = session_manager.get_session_memory(session_id)
    if not session_memory:
        print(f"[TOOL ERROR] Session memory not found for session: {session_id}")
        return json.dumps({
            "success": False,
            "error": "Session not found"
        })

    user_id = session_memory.user_id

    # Create BusinessCard model for validation
    try:
        business_card = BusinessCard(
            name=name,
            location=location,
            service_type=service_type,
            website=website if website and website.lower() not in ['none', 'not provided'] else None,
            social_links=social_links if social_links and social_links.lower() not in ['none', 'not provided'] else None,
        )
    except Exception as validation_error:
        print(f"[TOOL ERROR] Business card validation failed: {validation_error}")
        return json.dumps({
            "success": False,
            "error": f"Invalid business card data: {str(validation_error)}"
        })

    # Convert to dict for storage
    business_card_data = business_card.to_dict()

    print(f"[TOOL] save_business_card called for user: {user_id}")
    print(f"[TOOL] Business card data: {business_card_data}")
    print(f"[TOOL] Business card complete: {business_card.is_complete()}")

    try:
        # Import and use the save function from utils
        from utils.message_utils import save_business_card as save_business_card_util

        # Save to persistent storage (Firestore or in-memory)
        save_business_card_util(user_id, business_card_data)

        # Also save to session memory
        session_memory.set_business_card(business_card_data)

        print(f"[TOOL] ✓ Business card saved successfully for {name}")

        return json.dumps({
            "success": True,
            "message": f"Business card saved successfully for {name}",
            "business_card": business_card_data,
            "is_complete": business_card.is_complete()
        })
    except Exception as e:
        print(f"[TOOL ERROR] Failed to save business card: {e}")
        return json.dumps({
            "success": False,
            "error": str(e)
        })


def load_business_card_tool() -> str:
    """Load existing business card data from the database.

    Use this tool to check if a business card already exists for the current user
    before starting the onboarding process. This prevents asking for information
    the user has already provided in previous sessions.

    Returns:
        JSON string with business card data or error if not found
    """
    import json

    # Get session context from global storage (thread-safe)
    global _current_session_id
    with _context_lock:
        if not _current_session_id or _current_session_id not in _session_contexts:
            print("[TOOL ERROR] Session context not set - cannot load business card")
            return json.dumps({
                "success": False,
                "error": "Session context not available"
            })

        context = _session_contexts[_current_session_id]
        session_manager = context['session_manager']
        session_id = context['session_id']

    # Get user_id from session context
    if not session_manager or not session_id:
        print("[TOOL ERROR] Session context incomplete - cannot load business card")
        return json.dumps({
            "success": False,
            "error": "Session context incomplete"
        })

    session_memory = session_manager.get_session_memory(session_id)
    if not session_memory:
        print(f"[TOOL ERROR] Session memory not found for session: {session_id}")
        return json.dumps({
            "success": False,
            "error": "Session not found"
        })

    # First check session memory (the orchestrator may have injected a business card already)
    in_memory_card = session_memory.get_business_card()
    if in_memory_card:
        print(f"[TOOL] ✓ Business card found in session memory: {in_memory_card.get('name')}")
        return json.dumps({
            "success": True,
            "business_card": in_memory_card,
            "message": "Business card loaded from session"
        })

    user_id = session_memory.user_id

    print(f"[TOOL] load_business_card called for user: {user_id}")

    try:
        # Import and use the get function from utils
        from utils.message_utils import get_business_card as get_business_card_util

        # Load from persistent storage (Firestore or in-memory)
        business_card = get_business_card_util(user_id)

        if business_card:
            print(f"[TOOL] ✓ Business card found: {business_card.get('name')}")

            # Also load it into session memory so it's available for other agents
            session_memory.set_business_card(business_card)

            return json.dumps({
                "success": True,
                "business_card": business_card,
                "message": "Business card loaded successfully"
            })
        else:
            print(f"[TOOL] ℹ No business card found for user: {user_id}")
            return json.dumps({
                "success": False,
                "error": "No business card found",
                "message": "User has not completed onboarding yet"
            })
    except Exception as e:
        print(f"[TOOL ERROR] Failed to load business card: {e}")
        return json.dumps({
            "success": False,
            "error": str(e)
        })


# Create the tool instances
save_business_card = FunctionTool(save_business_card_tool)
load_business_card = FunctionTool(load_business_card_tool)
