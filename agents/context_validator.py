"""Context validation tool for agents.

This tool helps agents validate that required context/preconditions are met
before proceeding with their tasks. This prevents workflow errors where agents
skip steps or operate without necessary information.
"""
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class ValidationResult:
    """Result of context validation."""
    is_valid: bool
    missing_fields: List[str]
    error_message: Optional[str] = None

    def __bool__(self) -> bool:
        return self.is_valid


class ContextValidator:
    """Validates that required context fields are present in session."""

    @staticmethod
    def validate_business_card(session_context: Dict[str, Any]) -> ValidationResult:
        """
        Validate that business card exists in session context.

        Args:
            session_context: The session's shared context dictionary

        Returns:
            ValidationResult indicating if business card is present and valid
        """
        if not session_context:
            return ValidationResult(
                is_valid=False,
                missing_fields=["business_card"],
                error_message="No session context available"
            )

        business_card = session_context.get("business_card")

        if business_card is None:
            return ValidationResult(
                is_valid=False,
                missing_fields=["business_card"],
                error_message="Business card not found in session context. User must complete onboarding first."
            )

        # Validate required fields in business card
        required_fields = ["name", "location", "service_type"]
        missing = []

        for field in required_fields:
            value = business_card.get(field)
            if not value or value == "Not provided":
                missing.append(field)

        if missing:
            return ValidationResult(
                is_valid=False,
                missing_fields=missing,
                error_message=f"Business card is incomplete. Missing required fields: {', '.join(missing)}"
            )

        return ValidationResult(is_valid=True, missing_fields=[])

    @staticmethod
    def validate_required_fields(
        session_context: Dict[str, Any],
        required_fields: List[str]
    ) -> ValidationResult:
        """
        Validate that specific fields exist in session context.

        Args:
            session_context: The session's shared context dictionary
            required_fields: List of field names that must be present

        Returns:
            ValidationResult indicating if all required fields are present
        """
        if not session_context:
            return ValidationResult(
                is_valid=False,
                missing_fields=required_fields,
                error_message="No session context available"
            )

        missing = []
        for field in required_fields:
            if field not in session_context or session_context[field] is None:
                missing.append(field)

        if missing:
            return ValidationResult(
                is_valid=False,
                missing_fields=missing,
                error_message=f"Missing required context fields: {', '.join(missing)}"
            )

        return ValidationResult(is_valid=True, missing_fields=[])


# Example usage patterns for agent instructions

EXAMPLE_ONBOARDING_CHECK = """
## CRITICAL: Check Business Card First

**BEFORE doing anything else, check the session context for existing business card information.**

Use the context validator to check:

```python
from agents.context_validator import ContextValidator

result = ContextValidator.validate_business_card(session_context)

if result.is_valid:
    # Business card exists and is complete
    # Acknowledge user and confirm onboarding is complete
    return "Welcome back! I see we already have your details for [Business Name]..."
else:
    # Business card missing or incomplete
    # Proceed with onboarding to collect missing information
    pass
```
"""

EXAMPLE_CAMPAIGN_BRIEF_CHECK = """
## Precondition: Business Card Required

**This agent requires business card information to create personalized campaign briefs.**

Check preconditions before proceeding:

```python
from agents.context_validator import ContextValidator

# Validate business card exists
result = ContextValidator.validate_business_card(session_context)

if not result.is_valid:
    # Redirect to onboarding agent
    return {
        "error": "Business card required",
        "message": result.error_message,
        "redirect_to": "onboarding_agent"
    }

# Business card is valid, proceed with campaign brief creation
business_card = session_context["business_card"]
# Use business_card.name, business_card.location, etc.
```
"""

EXAMPLE_CREATOR_FINDER_CHECK = """
## Precondition: Campaign Brief Required

**This agent requires a campaign brief to find matching creators.**

Check preconditions before proceeding:

```python
from agents.context_validator import ContextValidator

# Validate required fields exist
result = ContextValidator.validate_required_fields(
    session_context,
    required_fields=["business_card", "campaign_brief"]
)

if not result.is_valid:
    missing = result.missing_fields
    if "business_card" in missing:
        # Redirect to onboarding
        return {"redirect_to": "onboarding_agent", "message": result.error_message}
    elif "campaign_brief" in missing:
        # Redirect to campaign brief agent
        return {"redirect_to": "campaign_brief_agent", "message": result.error_message}

# All preconditions met, proceed with creator search
```
"""
