"""Gmail API service for sending outreach emails.

This service handles:
- Gmail API OAuth 2.0 authentication
- Sending HTML emails with deep links
- JWT token generation for influencer responses
"""
import os
import base64
import jwt
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict, Any
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


# Gmail API scopes - we need send permission
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

# JWT secret for signing response tokens (should be in environment variable)
JWT_SECRET = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-this')

# Base URL for deep links (will be the deployed Cloud Run URL)
BASE_URL = os.getenv('BASE_URL', 'http://localhost:8000')


class GmailService:
    """Service for sending emails via Gmail API."""

    def __init__(self, credentials_path: str = 'gmail_credentials.json'):
        """Initialize Gmail service with OAuth credentials.

        Args:
            credentials_path: Path to the OAuth 2.0 credentials JSON file
        """
        self.credentials_path = credentials_path
        self.token_path = 'gmail_token.json'
        self.service = None

    def authenticate(self) -> None:
        """Authenticate with Gmail API using OAuth 2.0.

        This will open a browser for first-time authentication and save
        the token for future use.
        """
        creds = None

        # Load existing token if available
        if os.path.exists(self.token_path):
            creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)

        # If no valid credentials, initiate OAuth flow
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                # Refresh expired token
                creds.refresh(Request())
            else:
                # First-time authentication
                if not os.path.exists(self.credentials_path):
                    raise FileNotFoundError(
                        f"Gmail credentials file not found at {self.credentials_path}. "
                        "Please download OAuth 2.0 credentials from Google Cloud Console."
                    )

                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, SCOPES
                )
                creds = flow.run_local_server(port=8080)

            # Save credentials for next run
            with open(self.token_path, 'w') as token:
                token.write(creds.to_json())

        # Build Gmail API service
        self.service = build('gmail', 'v1', credentials=creds)
        print("[GmailService] Successfully authenticated with Gmail API")

    def generate_response_token(
        self,
        session_id: str,
        creator_email: str,
        creator_name: str,
        response_type: str,
        user_id: str
    ) -> str:
        """Generate a JWT token for influencer response deep link.

        Args:
            session_id: Session ID for the outreach campaign
            creator_email: Influencer's email address
            creator_name: Influencer's name
            response_type: Type of response (interested/not_interested/need_info)
            user_id: User ID of the campaign owner

        Returns:
            JWT token string
        """
        payload = {
            'session_id': session_id,
            'creator_email': creator_email,
            'creator_name': creator_name,
            'response_type': response_type,
            'user_id': user_id,
            'exp': datetime.utcnow() + timedelta(days=30),  # 30-day expiration
            'iat': datetime.utcnow()
        }

        token = jwt.encode(payload, JWT_SECRET, algorithm='HS256')
        return token

    def create_email_html(self, outreach_email: Dict[str, Any]) -> str:
        """Create HTML email content with deep links.

        Args:
            outreach_email: Dictionary with campaign details (session_id, creator_email, creator_name, etc.)

        Returns:
            HTML string for email body
        """
        # Generate response tokens
        token_interested = self.generate_response_token(
            outreach_email['session_id'],
            outreach_email['creator_email'],
            outreach_email['creator_name'],
            'interested',
            outreach_email['user_id']
        )

        token_not_interested = self.generate_response_token(
            outreach_email['session_id'],
            outreach_email['creator_email'],
            outreach_email['creator_name'],
            'not_interested',
            outreach_email['user_id']
        )

        token_need_info = self.generate_response_token(
            outreach_email['session_id'],
            outreach_email['creator_email'],
            outreach_email['creator_name'],
            'need_info',
            outreach_email['user_id']
        )

        # Create deep link URLs
        link_interested = f"{BASE_URL}/api/influencer-response?token={token_interested}"
        link_not_interested = f"{BASE_URL}/api/influencer-response?token={token_not_interested}"
        link_need_info = f"{BASE_URL}/api/influencer-response?token={token_need_info}"

        html = f"""
        <html>
          <head>
            <style>
              body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
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
              .snapshot {{
                background-color: #f9f9f9;
                padding: 15px;
                border-left: 4px solid #4285f4;
                margin: 20px 0;
              }}
              .snapshot-item {{
                margin: 8px 0;
              }}
              .buttons {{
                margin: 30px 0;
                text-align: center;
              }}
              .btn {{
                display: inline-block;
                padding: 12px 24px;
                margin: 8px;
                text-decoration: none;
                border-radius: 5px;
                font-weight: bold;
                font-size: 14px;
              }}
              .btn-yes {{
                background-color: #34a853;
                color: white;
              }}
              .btn-no {{
                background-color: #ea4335;
                color: white;
              }}
              .btn-info {{
                background-color: #fbbc04;
                color: #333;
              }}
              .footer {{
                margin-top: 30px;
                padding-top: 20px;
                border-top: 1px solid #ddd;
                font-size: 12px;
                color: #666;
              }}
            </style>
          </head>
          <body>
            <div class="header">
              <h2>Paid Collaboration Opportunity With {outreach_email['brand_name']}</h2>
            </div>

            <p>Hi {outreach_email['creator_name']},</p>

            <p>I'm Creo AI, reaching out on behalf of <strong>{outreach_email['brand_name']}</strong>,
            a {outreach_email['brand_description']}. We think you're potentially a strong fit for a
            paid creator partnership.</p>

            <div class="snapshot">
              <h3>Quick Snapshot:</h3>
              <div class="snapshot-item"><strong>Platform:</strong> {outreach_email['platform']}</div>
              <div class="snapshot-item"><strong>Location:</strong> {outreach_email['location']}</div>
              <div class="snapshot-item"><strong>Niche:</strong> {outreach_email['niche']}</div>
              <div class="snapshot-item"><strong>Goal:</strong> {outreach_email['goal']}</div>
              <div class="snapshot-item"><strong>Budget:</strong> up to ${outreach_email['budget_per_creator']:,.0f} per creator</div>
            </div>

            <p><strong>Are you open to exploring this collaboration?</strong></p>

            <div class="buttons">
              <a href="{link_interested}" class="btn btn-yes">✔ Yes, interested</a><br/>
              <a href="{link_not_interested}" class="btn btn-no">✖ Not interested</a><br/>
              <a href="{link_need_info}" class="btn btn-info">❓ Need more info</a>
            </div>

            <p>If you're interested, we'll send a short onboarding link next.</p>

            <p>Thanks,<br/>
            <strong>Creo AI</strong> for {outreach_email['brand_name']}</p>

            <div class="footer">
              <p>This is an automated collaboration request. Please click one of the buttons above to respond.</p>
            </div>
          </body>
        </html>
        """

        return html

    def send_email(
        self,
        outreach_email: Dict[str, Any],
        sender_email: str = 'oronmozes@gmail.com'
    ) -> Optional[str]:
        """Send outreach email via Gmail API.

        Args:
            outreach_email: Dictionary with campaign details
            sender_email: Email address to send from (must match authenticated account)

        Returns:
            Gmail message ID if successful, None otherwise
        """
        if not self.service:
            self.authenticate()

        try:
            # Create email message
            message = MIMEMultipart('alternative')
            message['To'] = outreach_email['creator_email']
            message['From'] = sender_email
            message['Subject'] = f"Paid Collaboration Opportunity With {outreach_email['brand_name']}"

            # Create HTML part
            html_content = self.create_email_html(outreach_email)
            html_part = MIMEText(html_content, 'html')
            message.attach(html_part)

            # Encode message
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')

            # Send email
            send_message = self.service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()

            message_id = send_message.get('id')
            print(f"[GmailService] Email sent successfully to {outreach_email['creator_email']}, ID: {message_id}")

            return message_id

        except HttpError as error:
            print(f"[GmailService] Error sending email: {error}")
            return None
        except Exception as e:
            print(f"[GmailService] Unexpected error: {e}")
            return None

    @staticmethod
    def verify_response_token(token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode a JWT response token from influencer.

        Args:
            token: JWT token from deep link

        Returns:
            Decoded token payload if valid, None otherwise
        """
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            print("[GmailService] Token has expired")
            return None
        except jwt.InvalidTokenError as e:
            print(f"[GmailService] Invalid token: {e}")
            return None


# Global instance
gmail_service = GmailService()
