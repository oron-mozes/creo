"""Tools for the campaign brief agent to save campaign information."""
from google.adk.tools import FunctionTool


def save_campaign_brief_tool(
    goal: str,
    platform: str = "any",
    location: str = None,
    niche: str = None,
    budget_per_creator: float = None,
    num_creators: int = 1,
    business_name: str = None,
    product_info: str = None,
    audience_demographics: str = None,
    audience_interests: str = None
) -> str:
    """Save campaign brief information to the database.

    This tool saves the collected campaign brief after user confirmation.
    Call this tool when the user has confirmed all campaign details.

    Args:
        goal: The campaign objective/goal (required) - what the campaign aims to achieve
        platform: Social media platform(s) to target - Instagram/TikTok/YouTube/Facebook or "any" (default: "any")
        location: Campaign target location - can override business location (optional, auto-filled from business card)
        niche: Campaign niche/category - Food/Travel/Tech/Lifestyle etc (optional, auto-filled from business card)
        budget_per_creator: Maximum budget per creator in dollars (optional)
        num_creators: Number of creators to work with (default: 1)
        business_name: Business name (optional, auto-filled from business card)
        product_info: Specific product or campaign details (optional)
        audience_demographics: Target audience demographics - age, gender, location (optional)
        audience_interests: Target audience interests or characteristics (optional)

    Returns:
        Success message confirming the campaign brief was saved
    """
    # This is a placeholder - the actual saving happens in the server
    # The server will parse the tool call and save to database
    return f"Campaign brief saved successfully! Goal: {goal}"


# Create the tool instance
save_campaign_brief = FunctionTool(save_campaign_brief_tool)
