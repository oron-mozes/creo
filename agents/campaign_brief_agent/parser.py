"""Parser for extracting campaign brief information from agent responses."""
import json
import re
from typing import Optional, Dict, Any

from agents.campaign_brief_agent.models import CampaignBrief


def parse_campaign_brief_confirmation(text: str) -> Optional[CampaignBrief]:
    """
    Parse campaign brief confirmation from agent response text.

    Looks for the pattern:
    CAMPAIGN_BRIEF_CONFIRMATION:
    {
      "goal": "...",
      "location": "...",
      "platform": "...",
      "niche": "...",
      "budget_per_creator": 500.0,
      "num_creators": 3,
      "business_name": "...",
      "product_info": "...",
      "audience_demographics": "...",
      "audience_interests": "..."
    }

    Args:
        text: The agent response text

    Returns:
        CampaignBrief object if found, None otherwise
    """
    # Look for CAMPAIGN_BRIEF_CONFIRMATION marker
    pattern = r'CAMPAIGN_BRIEF_CONFIRMATION:\s*\n?\s*(\{.*?\})'
    match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)

    if not match:
        return None

    try:
        # Extract JSON part
        json_str = match.group(1)
        # Clean up the JSON string
        json_str = json_str.strip()

        # Parse JSON
        data = json.loads(json_str)

        # Create CampaignBrief object
        # Handle budget conversion (it might be a string or None)
        budget = data.get("budget_per_creator")
        if budget is not None:
            try:
                budget = float(budget)
            except (ValueError, TypeError):
                budget = None

        # Handle num_creators conversion
        num_creators = data.get("num_creators", 1)
        if num_creators is not None:
            try:
                num_creators = int(num_creators)
            except (ValueError, TypeError):
                num_creators = 1

        return CampaignBrief(
            goal=data.get("goal"),
            location=data.get("location"),
            platform=data.get("platform"),
            niche=data.get("niche"),
            budget_per_creator=budget,
            num_creators=num_creators,
            business_name=data.get("business_name"),
            product_info=data.get("product_info"),
            audience_demographics=data.get("audience_demographics"),
            audience_interests=data.get("audience_interests")
        )
    except (json.JSONDecodeError, KeyError, AttributeError, ValueError) as e:
        print(f"[CampaignBriefParser] Error parsing campaign brief: {e}")
        return None


def extract_campaign_brief_from_response(text: str) -> Dict[str, Any]:
    """
    Extract campaign brief information and return both the brief and cleaned text.

    Args:
        text: The agent response text

    Returns:
        Dictionary with:
        - campaign_brief: CampaignBrief object or None
        - cleaned_text: Text with campaign brief confirmation removed
        - has_confirmation: Boolean indicating if confirmation was found
    """
    campaign_brief = parse_campaign_brief_confirmation(text)

    if campaign_brief:
        # Remove the confirmation block from text
        # Pattern matches: CAMPAIGN_BRIEF_CONFIRMATION: followed by JSON object (with any whitespace/newlines)
        # Using .*? for non-greedy match to get everything until the closing brace
        pattern = r'CAMPAIGN_BRIEF_CONFIRMATION:\s*\{.*?\}'
        cleaned_text = re.sub(pattern, '', text, flags=re.DOTALL | re.IGNORECASE)

        # Clean up any extra whitespace left behind
        cleaned_text = re.sub(r'\n\s*\n\s*\n+', '\n\n', cleaned_text)  # Remove triple+ newlines
        cleaned_text = cleaned_text.strip()

        return {
            "campaign_brief": campaign_brief,
            "cleaned_text": cleaned_text,
            "has_confirmation": True
        }

    return {
        "campaign_brief": None,
        "cleaned_text": text,
        "has_confirmation": False
    }
