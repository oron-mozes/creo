"""Tools for the outreach message agent to send emails to influencers."""
from typing import Optional
from google.adk.tools import FunctionTool


def send_outreach_email_tool(
    creator_email: str,
    creator_name: str,
    personalized_message: Optional[str] = None
) -> str:
    """Send outreach email to an influencer via Gmail.

    This tool sends a professional collaboration request email to an influencer
    with deep links for them to respond (interested/not interested/need more info).

    The email includes:
    - Campaign details (platform, location, niche, goal, budget)
    - Brand information
    - Three response options via deep links

    IMPORTANT: Only call this tool AFTER:
    1. User has confirmed the influencer to contact
    2. Campaign brief is complete
    3. User approves sending the outreach

    Args:
        creator_email: Influencer's email address (required)
        creator_name: Influencer's name for personalization (required)
        personalized_message: Optional custom message to include (not currently used in template)

    Returns:
        Success message with next steps or error message
    """
    # This is a placeholder - the actual email sending happens in the server
    # The server will:
    # 1. Parse this tool call
    # 2. Get campaign brief and business card from session memory
    # 3. Create OutreachEmail model
    # 4. Use GmailService to send the email
    # 5. Store outreach record in Firestore campaigns collection
    # 6. Update session state to AWAITING_RESPONSE

    return (
        f"📧 Outreach email sent to {creator_name} ({creator_email})!\n\n"
        f"The email includes:\n"
        f"- Campaign details and budget\n"
        f"- Three response options (interested/not interested/need more info)\n\n"
        f"I'll notify you when {creator_name} responds. You can continue to review campaign "
        f"details while waiting for their response."
    )


# Create the tool instance
send_outreach_email = FunctionTool(send_outreach_email_tool)
