"""
Thread-safe session context storage for agent tools.
"""
from __future__ import annotations

import threading
from typing import Any, Dict, Optional, Tuple

_lock = threading.Lock()
_contexts: Dict[Tuple[str, str], Dict[str, Any]] = {}
_current_session: Dict[str, str] = {}


def set_context(agent_name: str, session_manager: Any, session_id: str, user_id: Optional[str] = None) -> None:
    with _lock:
        _contexts[(agent_name, session_id)] = {
            "session_manager": session_manager,
            "session_id": session_id,
            "user_id": user_id,
        }
        _current_session[agent_name] = session_id


def get_context(agent_name: str, session_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    with _lock:
        sid = session_id or _current_session.get(agent_name)
        if not sid:
            return None
        return _contexts.get((agent_name, sid))


def clear_context(agent_name: Optional[str] = None) -> None:
    global _contexts, _current_session
    with _lock:
        if agent_name is None:
            _contexts.clear()
            _current_session.clear()
        else:
            _contexts = {k: v for k, v in _contexts.items() if k[0] != agent_name}
            _current_session.pop(agent_name, None)
