"""Handlers for agent tool calls.

This module processes tool calls made by agents during conversation flow.
When agents call tools like save_business_card or send_outreach_email,
this handler executes the actual functionality.
"""
import re
from typing import Dict, Any, Optional
from datetime import datetime

from session_manager import SessionManager
from utils.gmail_utils import GmailService, gmail_service
from utils.message_utils import save_business_card, get_business_card
from agents.outreach_message_agent.models import OutreachEmail
from agents.outreach_message_agent.tools_auth_handler import handle_require_auth_for_outreach
from config.database import get_db


def extract_tool_call_from_response(response_text: str) -> Optional[Dict[str, Any]]:
    """Extract tool call information from agent response text.

    This function looks for tool call patterns in the agent's response.
    ADK framework may include tool call information in the response.

    Args:
        response_text: The agent's response text

    Returns:
        Dictionary with tool_name and parameters, or None if no tool call found
    """
    # Pattern to match tool calls like: [TOOL_CALL: tool_name(param1=value1, param2=value2)]
    # This is a simplified pattern - adjust based on actual ADK output format

    # For now, return None as we'll handle this differently
    # The ADK framework should provide tool calls in the event stream
    return None


def handle_send_outreach_email_tool(
    session_id: str,
    user_id: str,
    creator_email: str,
    creator_name: str,
    session_manager: SessionManager,
    personalized_message: Optional[str] = None
) -> Dict[str, Any]:
    """Handle the send_outreach_email tool call from outreach agent.

    This function:
    1. Gets campaign brief and business card from session memory
    2. Creates OutreachEmail model
    3. Sends email via Gmail API
    4. Updates session memory with sent email record
    5. Stores outreach record in Firestore

    Args:
        session_id: Session identifier
        user_id: User identifier
        creator_email: Influencer's email address
        creator_name: Influencer's name
        session_manager: Session manager instance
        personalized_message: Optional custom message (not used in template yet)

    Returns:
        Dictionary with success status and email_id
    """
    print(f"[TOOL_HANDLER] Processing send_outreach_email: {creator_name} ({creator_email})")

    # Require authenticated user (anon users lack contact details)
    # Allow only verified auth IDs (JWT-backed) for outreach: google_* or dev_*
    def _is_authenticated_uid(uid: str) -> bool:
        return uid.startswith("google_") or uid.startswith("dev_")

    if not user_id or not _is_authenticated_uid(user_id):
        print(f"[TOOL_HANDLER] BLOCKED: Outreach requires login (user_id={user_id})")
        return {
            'success': False,
            'error': 'Authentication required to send outreach emails. Please sign in first.',
            'auth_required': True,
        }

    # Get session memory
    session_memory = session_manager.get_session_memory(session_id)
    if not session_memory:
        print(f"[TOOL_HANDLER] ERROR: Session memory not found for session: {session_id}")
        return {
            'success': False,
            'error': 'Session not found'
        }

    # Get business card
    business_card = session_memory.get_business_card()
    if not business_card:
        print(f"[TOOL_HANDLER] ERROR: Business card not found in session")
        return {
            'success': False,
            'error': 'Business card not found. Please complete onboarding first.'
        }

    # Get campaign brief from session memory
    # TODO: Add campaign brief retrieval method to session_manager
    # For now, we'll use placeholder values
    campaign_brief = session_memory.get_agent_context('campaign_brief_agent')

    if not campaign_brief:
        print(f"[TOOL_HANDLER] ERROR: Campaign brief not found in session")
        return {
            'success': False,
            'error': 'Campaign brief not found. Please create a campaign brief first.'
        }

    # Extract campaign brief data
    brief_data = campaign_brief.get('brief', {})

    # Create OutreachEmail model
    try:
        outreach_email = OutreachEmail(
            creator_email=creator_email,
            creator_name=creator_name,
            brand_name=business_card.get('name', 'Unknown Business'),
            brand_description=business_card.get('service_type', 'a business'),
            platform=brief_data.get('platform', 'any platform'),
            location=brief_data.get('location', business_card.get('location', 'any location')),
            niche=brief_data.get('niche', 'general'),
            goal=brief_data.get('goal', 'brand awareness'),
            budget_per_creator=brief_data.get('budget_per_creator', 1000.0),
            session_id=session_id,
            user_id=user_id
        )
    except Exception as e:
        print(f"[TOOL_HANDLER] ERROR: Failed to create OutreachEmail model: {e}")
        return {
            'success': False,
            'error': f'Failed to create outreach email: {str(e)}'
        }

    # Send email via Gmail
    try:
        # Ensure Gmail service is authenticated
        if not gmail_service.service:
            gmail_service.authenticate()

        email_payload = outreach_email.to_dict()
        email_id = gmail_service.send_email(email_payload)

        if not email_id:
            print(f"[TOOL_HANDLER] ERROR: Failed to send email")
            return {
                'success': False,
                'error': 'Failed to send email via Gmail'
            }

        print(f"[TOOL_HANDLER] ✓ Email sent successfully, ID: {email_id}")

        # Update outreach email model with sent timestamp and email ID
        outreach_email.sent_at = datetime.utcnow()
        outreach_email.email_id = email_id

        # Update session memory
        session_memory.add_outreach_email(outreach_email.to_dict())

        # Store in Firestore campaigns collection
        db = get_db()
        if db is not None:
            try:
                # Create or update campaign document
                campaign_ref = db.collection('campaigns').document(session_id)
                campaign_ref.set({
                    'user_id': user_id,
                    'session_id': session_id,
                    'business_card': business_card,
                    'campaign_brief': brief_data,
                    'outreach_emails': {
                        creator_email: {
                            'creator_name': creator_name,
                            'creator_email': creator_email,
                            'sent_at': outreach_email.sent_at.isoformat(),
                            'email_id': email_id,
                            'status': 'awaiting_response',
                        }
                    },
                    'updated_at': datetime.utcnow().isoformat()
                }, merge=True)
                print(f"[TOOL_HANDLER] ✓ Outreach record saved to Firestore")
            except Exception as e:
                print(f"[TOOL_HANDLER] WARNING: Failed to save to Firestore: {e}")

        return {
            'success': True,
            'email_id': email_id,
            'creator_email': creator_email,
            'creator_name': creator_name
        }

    except Exception as e:
        print(f"[TOOL_HANDLER] ERROR: Failed to send email: {e}")
        return {
            'success': False,
            'error': f'Failed to send email: {str(e)}'
        }


def handle_tool_calls(
    response_text: str,
    session_id: str,
    user_id: str,
    session_manager: SessionManager
) -> Dict[str, Any]:
    """Main handler to detect and process tool calls from agent responses.

    This function checks if the agent's response contains a tool call
    and executes the appropriate handler.

    Args:
        response_text: The agent's response text
        session_id: Session identifier
        user_id: User identifier
        session_manager: Session manager instance

    Returns:
        Dictionary with tool execution results or None if no tool call
    """
    # Check for send_outreach_email tool call
    if 'send_outreach_email' in response_text.lower():
        print(f"[TOOL_HANDLER] Detected potential send_outreach_email tool call")
        return {
            'tool_detected': True,
            'tool_name': 'send_outreach_email',
            'note': 'Tool call detected but parameter extraction not implemented yet'
        }

    # Check for require_auth_for_outreach tool call
    if 'require_auth_for_outreach' in response_text.lower():
        print(f"[TOOL_HANDLER] Detected require_auth_for_outreach tool call")
        return {
            'tool_detected': True,
            'tool_name': 'require_auth_for_outreach',
            **handle_require_auth_for_outreach()
        }

    return {
        'tool_detected': False
    }
