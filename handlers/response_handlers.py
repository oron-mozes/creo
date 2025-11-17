"""Handlers for influencer responses via deep links."""
from typing import Dict, Any, Optional
from datetime import datetime

from session_manager import SessionManager
from agents.outreach_message_agent.models import InfluencerResponse, ResponseType
from utils.gmail_utils import GmailService
from config.database import get_db


def send_notification_email(
    user_email: str,
    influencer_response: InfluencerResponse,
    gmail_service: GmailService
) -> bool:
    """Send email notification to user about influencer response.

    Args:
        user_email: User's email address (oronmozes@gmail.com)
        influencer_response: The influencer's response data
        gmail_service: Gmail service instance

    Returns:
        True if email sent successfully, False otherwise
    """
    import base64
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart

    try:
        # Ensure Gmail service is authenticated
        if not gmail_service.service:
            gmail_service.authenticate()

        # Create email
        message = MIMEMultipart('alternative')
        message['To'] = user_email
        message['From'] = user_email  # Send from same address
        message['Subject'] = f"Influencer Response: {influencer_response.creator_name}"

        # Get user-friendly message
        status_message = influencer_response.get_user_friendly_message()

        # Create HTML content
        html_content = f"""
        <html>
          <head>
            <style>
              body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
              }}
              .container {{
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
              }}
              .header {{
                background-color: #f4f4f4;
                padding: 20px;
                border-radius: 5px;
                margin-bottom: 20px;
              }}
              .status {{
                font-size: 18px;
                font-weight: bold;
                margin: 20px 0;
              }}
              .status.interested {{
                color: #34a853;
              }}
              .status.not-interested {{
                color: #ea4335;
              }}
              .status.need-info {{
                color: #fbbc04;
              }}
              .details {{
                background-color: #f9f9f9;
                padding: 15px;
                border-left: 4px solid #4285f4;
                margin: 20px 0;
              }}
            </style>
          </head>
          <body>
            <div class="container">
              <div class="header">
                <h2>Influencer Response Received</h2>
              </div>

              <p class="status {influencer_response.response_type.value}">
                {status_message}
              </p>

              <div class="details">
                <p><strong>Creator:</strong> {influencer_response.creator_name}</p>
                <p><strong>Email:</strong> {influencer_response.creator_email}</p>
                <p><strong>Response Type:</strong> {influencer_response.response_type.value.replace('_', ' ').title()}</p>
                <p><strong>Responded At:</strong> {influencer_response.responded_at.strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
              </div>

              <p>
                Log in to your Creo dashboard to view full details and take next steps.
              </p>
            </div>
          </body>
        </html>
        """

        html_part = MIMEText(html_content, 'html')
        message.attach(html_part)

        # Encode and send
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        send_message = gmail_service.service.users().messages().send(
            userId='me',
            body={'raw': raw_message}
        ).execute()

        print(f"[RESPONSE_HANDLER] Notification email sent to {user_email}, ID: {send_message.get('id')}")
        return True

    except Exception as e:
        print(f"[RESPONSE_HANDLER] ERROR: Failed to send notification email: {e}")
        return False


def handle_influencer_response(
    token: str,
    session_manager: SessionManager,
    gmail_service: GmailService,
    user_email: str = 'oronmozes@gmail.com'
) -> Dict[str, Any]:
    """Handle influencer response from deep link click.

    This function:
    1. Verifies the JWT token
    2. Extracts response data
    3. Updates session memory
    4. Updates Firestore
    5. Sends email notification to user

    Args:
        token: JWT token from deep link
        session_manager: Session manager instance
        gmail_service: Gmail service instance
        user_email: User's email for notifications

    Returns:
        Dictionary with success status and response data
    """
    print(f"[RESPONSE_HANDLER] Processing influencer response token")

    # Verify token
    payload = GmailService.verify_response_token(token)
    if not payload:
        print(f"[RESPONSE_HANDLER] ERROR: Invalid or expired token")
        return {
            'success': False,
            'error': 'Invalid or expired response link'
        }

    # Extract data from token
    session_id = payload.get('session_id')
    creator_email = payload.get('creator_email')
    creator_name = payload.get('creator_name')
    response_type = payload.get('response_type')
    user_id = payload.get('user_id')

    print(f"[RESPONSE_HANDLER] Response from {creator_name} ({creator_email}): {response_type}")

    # Create InfluencerResponse model
    try:
        influencer_response = InfluencerResponse(
            response_type=ResponseType(response_type),
            creator_email=creator_email,
            creator_name=creator_name,
            session_id=session_id,
            user_id=user_id
        )
    except Exception as e:
        print(f"[RESPONSE_HANDLER] ERROR: Failed to create InfluencerResponse: {e}")
        return {
            'success': False,
            'error': f'Invalid response data: {str(e)}'
        }

    # Update session memory
    session_memory = session_manager.get_session_memory(session_id)
    if session_memory:
        session_memory.record_influencer_response(influencer_response.to_dict())
        print(f"[RESPONSE_HANDLER] ✓ Updated session memory")
    else:
        print(f"[RESPONSE_HANDLER] WARNING: Session memory not found for session: {session_id}")

    # Update Firestore
    db = get_db()
    if db is not None:
        try:
            campaign_ref = db.collection('campaigns').document(session_id)
            campaign_ref.set({
                'outreach_emails': {
                    creator_email: {
                        'status': response_type,
                        'responded_at': influencer_response.responded_at.isoformat(),
                    }
                },
                'influencer_responses': {
                    creator_email: influencer_response.to_dict()
                },
                'updated_at': datetime.utcnow().isoformat()
            }, merge=True)
            print(f"[RESPONSE_HANDLER] ✓ Updated Firestore")
        except Exception as e:
            print(f"[RESPONSE_HANDLER] WARNING: Failed to update Firestore: {e}")

    # Send email notification to user
    notification_sent = send_notification_email(user_email, influencer_response, gmail_service)

    return {
        'success': True,
        'response_type': response_type,
        'creator_name': creator_name,
        'creator_email': creator_email,
        'notification_sent': notification_sent,
        'message': influencer_response.get_user_friendly_message()
    }
