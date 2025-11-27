"""Shared content utilities for response parsing."""
from typing import List
from google.genai import types


def content_to_text(content: types.Content | None) -> str:
    """Extract concatenated text from a Content object."""
    if not content or not getattr(content, "parts", None):
        return ""
    texts: List[str] = []
    for part in content.parts:
        if getattr(part, "text", None):
            texts.append(part.text)
    return "\n".join(texts).strip()
