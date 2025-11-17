"""Workflow enums for Creo multi-agent system.

This module defines enums for workflow stages and agent-specific states
to ensure type safety and consistency across the codebase.
"""
from enum import Enum


class WorkflowStage(str, Enum):
    """Workflow stages in the Creo influencer marketing pipeline.

    These stages represent the shared state of the workflow and determine
    which agent should handle user requests.
    """
    ONBOARDING = "onboarding"
    CAMPAIGN_BRIEF = "campaign_brief"
    CREATOR_FINDER = "creator_finder"
    OUTREACH_MESSAGE = "outreach_message"
    CAMPAIGN_BUILDER = "campaign_builder"


class OnboardingStatus(str, Enum):
    """Agent-specific status for the onboarding agent.

    This represents the internal state of the onboarding agent and is NOT
    shared with other agents or the orchestrator.
    """
    COLLECTING = "collecting"  # Gathering business information
    AWAITING_CONFIRMATION = "awaiting_confirmation"  # Waiting for user to confirm details
    COMPLETE = "complete"  # Onboarding finished


class ExtractedField(str, Enum):
    """Business card fields that can be extracted during onboarding.

    These fields are tracked in the onboarding agent's extraction history
    to avoid asking for the same information multiple times.
    """
    BUSINESS_NAME = "name"
    WEBSITE = "website"
    SOCIAL_LINKS = "social_links"
    LOCATION = "location"
    SERVICE_TYPE = "service_type"
