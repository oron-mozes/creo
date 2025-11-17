#!/usr/bin/env python3
"""Test script for onboarding agent extraction memory."""

from session_manager import SessionMemory
from workflow_enums import ExtractedField, OnboardingStatus

def test_extraction_memory():
    """Test the onboarding agent extraction memory functionality."""

    print("=" * 80)
    print("TESTING ONBOARDING AGENT EXTRACTION MEMORY")
    print("=" * 80)

    # Create a session memory
    session_memory = SessionMemory(session_id="test_session_123", user_id="test_user_456")
    print("\n✓ Created session memory")

    # Test 1: Initialize onboarding context
    print("\n" + "=" * 80)
    print("TEST 1: Initialize Onboarding Context")
    print("=" * 80)
    session_memory.initialize_onboarding_context()
    status = session_memory.get_onboarding_status()
    print(f"Initial status: {status}")
    assert status == OnboardingStatus.COLLECTING, "Should start with COLLECTING status"
    print("✓ Onboarding context initialized with COLLECTING status")

    # Test 2: Add extractions
    print("\n" + "=" * 80)
    print("TEST 2: Add Extractions")
    print("=" * 80)

    # User provides website
    print("\nUser message: 'My website is https://almacafe.co.il'")
    session_memory.add_extraction(
        field=ExtractedField.WEBSITE,
        value="https://almacafe.co.il",
        message_id="msg_001",
        source="user_input"
    )

    # Agent searches and extracts from Google
    print("\nAgent performs Google search...")
    session_memory.add_extraction(
        field=ExtractedField.BUSINESS_NAME,
        value="Alma Cafe",
        message_id="msg_001",
        source="google_search"
    )

    session_memory.add_extraction(
        field=ExtractedField.LOCATION,
        value="Rehovot, Israel",
        message_id="msg_001",
        source="google_search"
    )

    session_memory.add_extraction(
        field=ExtractedField.SERVICE_TYPE,
        value="Coffee shop",
        message_id="msg_001",
        source="google_search"
    )

    print("\n✓ Added 4 extractions")

    # Test 3: Check extracted fields
    print("\n" + "=" * 80)
    print("TEST 3: Check Extracted Fields")
    print("=" * 80)

    # Check if fields are extracted
    has_name = session_memory.has_extracted_field(ExtractedField.BUSINESS_NAME)
    has_website = session_memory.has_extracted_field(ExtractedField.WEBSITE)
    has_location = session_memory.has_extracted_field(ExtractedField.LOCATION)
    has_service = session_memory.has_extracted_field(ExtractedField.SERVICE_TYPE)
    has_social = session_memory.has_extracted_field(ExtractedField.SOCIAL_LINKS)

    print(f"Has business name: {has_name} ✓")
    print(f"Has website: {has_website} ✓")
    print(f"Has location: {has_location} ✓")
    print(f"Has service type: {has_service} ✓")
    print(f"Has social links: {has_social} (expected: False)")

    assert has_name == True
    assert has_website == True
    assert has_location == True
    assert has_service == True
    assert has_social == False
    print("\n✓ Field checks working correctly")

    # Test 4: Get extracted values
    print("\n" + "=" * 80)
    print("TEST 4: Get Extracted Values")
    print("=" * 80)

    name = session_memory.get_extracted_field(ExtractedField.BUSINESS_NAME)
    website = session_memory.get_extracted_field(ExtractedField.WEBSITE)
    location = session_memory.get_extracted_field(ExtractedField.LOCATION)
    service = session_memory.get_extracted_field(ExtractedField.SERVICE_TYPE)
    social = session_memory.get_extracted_field(ExtractedField.SOCIAL_LINKS)

    print(f"Business name: {name}")
    print(f"Website: {website}")
    print(f"Location: {location}")
    print(f"Service type: {service}")
    print(f"Social links: {social}")

    assert name == "Alma Cafe"
    assert website == "https://almacafe.co.il"
    assert location == "Rehovot, Israel"
    assert service == "Coffee shop"
    assert social is None
    print("\n✓ All extracted values correct")

    # Test 5: Get extraction history
    print("\n" + "=" * 80)
    print("TEST 5: Get Extraction History")
    print("=" * 80)

    extractions = session_memory.get_extractions()
    print(f"\nTotal extractions: {len(extractions)}")

    for i, ext in enumerate(extractions, 1):
        print(f"\nExtraction {i}:")
        print(f"  Field: {ext['field']}")
        print(f"  Value: {ext['value']}")
        print(f"  Message ID: {ext['message_id']}")
        print(f"  Source: {ext['source']}")
        print(f"  Timestamp: {ext['timestamp']}")

    assert len(extractions) == 4
    assert extractions[0]['field'] == 'website'
    assert extractions[0]['source'] == 'user_input'
    assert extractions[1]['field'] == 'name'
    assert extractions[1]['source'] == 'google_search'
    print("\n✓ Extraction history correct")

    # Test 6: Update onboarding status
    print("\n" + "=" * 80)
    print("TEST 6: Update Onboarding Status")
    print("=" * 80)

    session_memory.set_onboarding_status(OnboardingStatus.AWAITING_CONFIRMATION)
    status = session_memory.get_onboarding_status()
    print(f"Updated status: {status}")
    assert status == OnboardingStatus.AWAITING_CONFIRMATION
    print("✓ Status updated to AWAITING_CONFIRMATION")

    # Test 7: Avoid redundant questions (use case)
    print("\n" + "=" * 80)
    print("TEST 7: Avoid Redundant Questions (Use Case)")
    print("=" * 80)

    print("\nScenario: Agent wants to ask for business name...")
    if session_memory.has_extracted_field(ExtractedField.BUSINESS_NAME):
        existing_name = session_memory.get_extracted_field(ExtractedField.BUSINESS_NAME)
        print(f"✓ Already extracted: {existing_name}")
        print("✓ Agent skips asking for name (no redundant question)")
    else:
        print("Would ask user for business name")

    print("\nScenario: Agent wants to ask for social links...")
    if session_memory.has_extracted_field(ExtractedField.SOCIAL_LINKS):
        existing_social = session_memory.get_extracted_field(ExtractedField.SOCIAL_LINKS)
        print(f"Already extracted: {existing_social}")
    else:
        print("✓ Not extracted yet - agent can ask for social links")

    # Test 8: Verify shared vs agent-specific separation
    print("\n" + "=" * 80)
    print("TEST 8: Verify Shared vs Agent-Specific Separation")
    print("=" * 80)

    # Check shared context
    print("\nShared context contains:")
    print(f"  - session_id: {session_memory.shared_context['session_id']}")
    print(f"  - user_id: {session_memory.shared_context['user_id']}")
    print(f"  - messages: {len(session_memory.shared_context['messages'])} messages")
    print(f"  - business_card: {session_memory.shared_context['business_card']}")
    print(f"  - workflow_state.stage: {session_memory.shared_context['workflow_state']['stage']}")

    # Check agent-specific context
    print("\nAgent-specific context (onboarding_agent) contains:")
    onboarding_context = session_memory.agent_contexts['onboarding_agent']
    print(f"  - status: {onboarding_context['status']}")
    print(f"  - extractions: {len(onboarding_context['extractions'])} records")
    print(f"  - extracted_fields: {len(onboarding_context['extracted_fields'])} fields")

    # Verify extractions are NOT in shared context
    assert 'extractions' not in session_memory.shared_context
    print("\n✓ Extractions correctly stored in agent-specific context (not shared)")

    # Test 9: String-based field access (backwards compatibility)
    print("\n" + "=" * 80)
    print("TEST 9: String-Based Field Access")
    print("=" * 80)

    # Can use strings instead of enums
    name_via_string = session_memory.get_extracted_field('name')
    has_location_via_string = session_memory.has_extracted_field('location')

    print(f"Get field using string 'name': {name_via_string}")
    print(f"Check field using string 'location': {has_location_via_string}")

    assert name_via_string == "Alma Cafe"
    assert has_location_via_string == True
    print("\n✓ String-based access works (backwards compatible)")

    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print("✓ All tests passed!")
    print("\nExtraction memory features verified:")
    print("  ✓ Initialize onboarding context")
    print("  ✓ Add extractions with field, value, message_id, source")
    print("  ✓ Check if field extracted (has_extracted_field)")
    print("  ✓ Get extracted field value (get_extracted_field)")
    print("  ✓ Get full extraction history (get_extractions)")
    print("  ✓ Update onboarding status")
    print("  ✓ Avoid redundant questions use case")
    print("  ✓ Shared vs agent-specific separation")
    print("  ✓ String-based field access (backwards compatible)")
    print("\n" + "=" * 80)

if __name__ == "__main__":
    test_extraction_memory()
