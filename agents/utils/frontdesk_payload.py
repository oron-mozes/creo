"""Utilities for building structured payloads to frontdesk."""

from typing import Any, Dict, Optional


def build_frontdesk_payload(
    stage: str,
    user_request: str,
    specialist_response: str,
    auth_required: bool = False,
    gallery: Optional[list] = None,
    extras: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Create a structured payload for the frontdesk agent.

    Args:
        stage: Current workflow stage label
        user_request: Last user message content
        specialist_response: Text from the specialist agent
        auth_required: Whether to hint the client to prompt login
        gallery: Optional list of gallery items to surface in UI
        extras: Optional extra fields to include

    Returns:
        Dict payload to pass to frontdesk
    """
    payload = {
        "stage": stage,
        "user_request": user_request or "No user text available.",
        "specialist_response": specialist_response or "No specialist response was generated.",
        "auth_required": auth_required,
        "gallery": gallery or [],
    }
    if extras:
        payload.update(extras)
    return payload


def to_frontdesk_string(payload: Dict[str, Any]) -> str:
    """Render a structured payload to a string for frontdesk LLM consumption."""
    parts = [
        f"Workflow stage: {payload.get('stage', 'unspecified stage')}",
        f"User request: {payload.get('user_request', 'No user text available.')}",
        f"Specialist response: {payload.get('specialist_response', 'No specialist response was generated.')}",
    ]
    if payload.get("auth_required"):
        parts.append("Auth required: true")
    gallery = payload.get("gallery") or []
    if gallery:
        parts.append(f"Gallery items: {len(gallery)}")
    extras = {k: v for k, v in payload.items() if k not in {"stage", "user_request", "specialist_response", "auth_required", "gallery"}}
    if extras:
        parts.append(f"Extras: {extras}")
    return " | ".join(parts)

