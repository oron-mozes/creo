"""Shared content utilities for response parsing."""

from typing import List, Any
from google.genai import types


def content_to_text(content: types.Content | None) -> str:
    """Extract concatenated text from a Content object."""
    if not content or not getattr(content, "parts", None):
        return ""
    texts: List[str] = []
    parts = getattr(content, "parts", None)
    if not parts:
        return ""
    for part in parts:
        text: Any = getattr(part, "text", None)
        if isinstance(text, str):
            texts.append(text)
        elif text is not None:
            texts.append(str(text))
    return "\n".join(texts).strip()
