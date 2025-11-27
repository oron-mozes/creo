"""Tools for the onboarding agent to collect and save business information."""
from typing import Optional, Dict, Any
from google.adk.tools import FunctionTool
from agents.onboarding_agent.models import BusinessCard
from agents.session_context import set_context as set_shared_context, get_context as get_shared_context

def set_session_context(session_manager, session_id: str):
    """Set the session context for tools to access user_id."""
    set_shared_context("onboarding_agent", session_manager, session_id)


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

    context = get_shared_context("onboarding_agent")
    if not context:
        print("[TOOL ERROR] Session context not set - cannot save business card")
        return json.dumps({
            "success": False,
            "error": "Session context not available"
        })
    session_manager = context.get('session_manager')
    session_id = context.get('session_id')

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


def normalize_url_tool(url: str) -> str:
    """Normalize a URL or domain to a standard format.

    This tool converts various URL formats into a normalized domain name:
    - Adds 'https://' if no protocol is present
    - Removes www. prefix
    - Removes paths, query parameters, and fragments
    - Handles social media URLs and naked domains

    Examples:
        - "example.com" → "https://example.com"
        - "www.example.com/about" → "https://example.com"
        - "http://example.com?param=value" → "https://example.com"
        - "@username" → "@username" (preserved for social handles)

    Args:
        url: The URL or domain to normalize

    Returns:
        JSON string with normalized URL
    """
    import json
    from urllib.parse import urlparse

    print(f"[TOOL] normalize_url called with: {url}")

    # Preserve social media handles (start with @)
    if url.strip().startswith('@'):
        print(f"[TOOL] Preserving social handle: {url}")
        return json.dumps({
            "success": True,
            "original": url,
            "normalized": url.strip(),
            "type": "social_handle"
        })

    # Clean the input
    url = url.strip()

    # Add protocol if missing
    if not url.startswith(('http://', 'https://')):
        url = f'https://{url}'

    try:
        # Parse the URL
        parsed = urlparse(url)

        # Get the domain (netloc)
        domain = parsed.netloc or parsed.path

        # Remove www. prefix
        if domain.startswith('www.'):
            domain = domain[4:]

        # Construct normalized URL (always https, no path)
        normalized = f'https://{domain}'

        print(f"[TOOL] ✓ URL normalized: {url} → {normalized}")

        return json.dumps({
            "success": True,
            "original": url,
            "normalized": normalized,
            "domain": domain,
            "type": "url"
        })
    except Exception as e:
        print(f"[TOOL ERROR] Failed to normalize URL: {e}")
        return json.dumps({
            "success": False,
            "error": str(e),
            "original": url
        })


# Create the tool instances
save_business_card = FunctionTool(save_business_card_tool)
load_business_card = FunctionTool(load_business_card_tool)
normalize_url = FunctionTool(normalize_url_tool)
