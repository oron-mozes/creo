"""Server-side handler for outreach auth requirement."""
from __future__ import annotations

from typing import Any, Dict


def handle_require_auth_for_outreach() -> Dict[str, Any]:
    """Return a marker payload to tell the client to prompt for auth."""
    return {
        'success': False,
        'auth_required': True,
        'error': 'Authentication required to continue outreach.',
    }
