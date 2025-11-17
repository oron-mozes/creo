"""Tools for the onboarding agent to collect and save business information."""
from typing import Optional
from google.adk.tools import FunctionTool


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
        Success message confirming the business card was saved
    """
    # This is a placeholder - the actual saving happens in the server
    # The server will parse the tool call and save to database
    return f"Business card saved successfully for {name}!"


# Create the tool instance
save_business_card = FunctionTool(save_business_card_tool)
