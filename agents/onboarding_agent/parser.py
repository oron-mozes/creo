"""Parser for extracting business card information from agent responses."""
import json
import re
from typing import Optional, Dict, Any

from agents.onboarding_agent.models import BusinessCard


def parse_business_card_confirmation(text: str) -> Optional[BusinessCard]:
    """
    Parse business card confirmation from agent response text.
    
    Looks for the pattern:
    BUSINESS_CARD_CONFIRMATION:
    {
      "name": "...",
      "website": "...",
      "social_links": "...",
      "location": "...",
      "service_type": "..."
    }
    
    Args:
        text: The agent response text
        
    Returns:
        BusinessCard object if found, None otherwise
    """
    # Look for BUSINESS_CARD_CONFIRMATION marker
    pattern = r'BUSINESS_CARD_CONFIRMATION:\s*\n?\s*(\{.*?\})'
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
        
        # Create BusinessCard object
        return BusinessCard(
            name=data.get("name"),
            website=data.get("website"),
            social_links=data.get("social_links"),
            location=data.get("location"),
            service_type=data.get("service_type")
        )
    except (json.JSONDecodeError, KeyError, AttributeError) as e:
        print(f"[BusinessCardParser] Error parsing business card: {e}")
        return None


def extract_business_card_from_response(text: str) -> Dict[str, Any]:
    """
    Extract business card information and return both the card and cleaned text.
    
    Args:
        text: The agent response text
        
    Returns:
        Dictionary with:
        - business_card: BusinessCard object or None
        - cleaned_text: Text with business card confirmation removed
        - has_confirmation: Boolean indicating if confirmation was found
    """
    business_card = parse_business_card_confirmation(text)
    
    if business_card:
        # Remove the confirmation block from text
        # Pattern matches: BUSINESS_CARD_CONFIRMATION: followed by JSON object (with any whitespace/newlines)
        # Using .*? for non-greedy match to get everything until the closing brace
        pattern = r'BUSINESS_CARD_CONFIRMATION:\s*\{.*?\}'
        cleaned_text = re.sub(pattern, '', text, flags=re.DOTALL | re.IGNORECASE)

        # Clean up any extra whitespace left behind
        cleaned_text = re.sub(r'\n\s*\n\s*\n+', '\n\n', cleaned_text)  # Remove triple+ newlines
        cleaned_text = cleaned_text.strip()
        
        return {
            "business_card": business_card,
            "cleaned_text": cleaned_text,
            "has_confirmation": True
        }
    
    return {
        "business_card": None,
        "cleaned_text": text,
        "has_confirmation": False
    }
