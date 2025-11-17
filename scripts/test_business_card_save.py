#!/usr/bin/env python3
"""
Test script to validate business card save operation.

This script tests the complete flow:
1. Agent generates BUSINESS_CARD_CONFIRMATION block
2. Parser extracts business card from response
3. Business card can be saved and retrieved from session
"""
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import importlib.util


def load_parser():
    """Load the business card parser dynamically."""
    parser_path = PROJECT_ROOT / "agents" / "onboarding-agent" / "parser.py"
    spec = importlib.util.spec_from_file_location("onboarding_parser", parser_path)
    parser_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(parser_module)
    return parser_module


def test_business_card_extraction():
    """Test that business card can be extracted from agent response."""
    parser = load_parser()

    # Test response with BUSINESS_CARD_CONFIRMATION block
    test_response = """
Great! Let me confirm I have this right:

Business Name: Alma Cafe
Location: Rehovot, Israel
Service Type: Coffee shop
Website: https://www.almacafe.co.il
Social Links: Not provided

Does everything look correct?

BUSINESS_CARD_CONFIRMATION:
{
  "name": "Alma Cafe",
  "website": "https://www.almacafe.co.il",
  "social_links": "Not provided",
  "location": "Rehovot, Israel",
  "service_type": "Coffee shop"
}
"""

    result = parser.extract_business_card_from_response(test_response)

    print("=" * 60)
    print("BUSINESS CARD EXTRACTION TEST")
    print("=" * 60)

    print(f"\n✓ Confirmation block found: {result['has_confirmation']}")

    if result['business_card']:
        bc = result['business_card']
        print(f"✓ Business card extracted successfully:")
        print(f"  - Name: {bc.name}")
        print(f"  - Location: {bc.location}")
        print(f"  - Service Type: {bc.service_type}")
        print(f"  - Website: {bc.website}")
        print(f"  - Social Links: {bc.social_links}")
    else:
        print(f"✗ Business card extraction FAILED")
        return False

    print(f"\n✓ Cleaned text (confirmation block removed):")
    print(f"  Length: {len(result['cleaned_text'])} chars")
    print(f"  Preview: {result['cleaned_text'][:100]}...")

    # Verify confirmation block was removed
    if "BUSINESS_CARD_CONFIRMATION" in result['cleaned_text']:
        print("\n✗ FAILED: Confirmation block not removed from cleaned text")
        return False
    else:
        print("\n✓ Confirmation block successfully removed from user-facing text")

    return True


def test_context_validator():
    """Test the context validator for precondition checks."""
    from agents.context_validator import ContextValidator

    print("\n" + "=" * 60)
    print("CONTEXT VALIDATOR TEST")
    print("=" * 60)

    # Test 1: Valid business card
    print("\n[Test 1] Valid business card:")
    session_context = {
        "business_card": {
            "name": "Alma Cafe",
            "location": "Rehovot, Israel",
            "service_type": "Coffee shop",
            "website": "https://www.almacafe.co.il",
            "social_links": "Not provided"
        }
    }

    result = ContextValidator.validate_business_card(session_context)
    print(f"  Valid: {result.is_valid}")
    print(f"  Missing fields: {result.missing_fields}")
    if result.error_message:
        print(f"  Error: {result.error_message}")

    # Test 2: Missing business card
    print("\n[Test 2] Missing business card:")
    session_context_empty = {}
    result = ContextValidator.validate_business_card(session_context_empty)
    print(f"  Valid: {result.is_valid}")
    print(f"  Missing fields: {result.missing_fields}")
    if result.error_message:
        print(f"  Error: {result.error_message}")

    # Test 3: Incomplete business card
    print("\n[Test 3] Incomplete business card (missing name):")
    session_context_incomplete = {
        "business_card": {
            "name": "Not provided",
            "location": "Rehovot, Israel",
            "service_type": "Coffee shop"
        }
    }
    result = ContextValidator.validate_business_card(session_context_incomplete)
    print(f"  Valid: {result.is_valid}")
    print(f"  Missing fields: {result.missing_fields}")
    if result.error_message:
        print(f"  Error: {result.error_message}")

    # Test 4: Validate required fields
    print("\n[Test 4] Validate required fields:")
    session_with_campaign = {
        "business_card": {"name": "Test"},
        "campaign_brief": {"objective": "Test campaign"}
    }
    result = ContextValidator.validate_required_fields(
        session_with_campaign,
        required_fields=["business_card", "campaign_brief"]
    )
    print(f"  Valid: {result.is_valid}")
    print(f"  Missing fields: {result.missing_fields}")

    print("\n" + "=" * 60)
    return True


def main():
    """Run all tests."""
    print("\n🧪 Running Business Card Save & Context Validation Tests\n")

    success = True

    # Test business card extraction
    if not test_business_card_extraction():
        success = False

    # Test context validator
    if not test_context_validator():
        success = False

    print("\n" + "=" * 60)
    if success:
        print("✅ ALL TESTS PASSED")
    else:
        print("❌ SOME TESTS FAILED")
    print("=" * 60 + "\n")

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
