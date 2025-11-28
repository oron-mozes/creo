"""Database configuration and initialization."""
import os
import importlib
from typing import Optional, Any

# Import firestore dynamically to avoid missing type stubs during typing
firestore: Any
try:
    firestore = importlib.import_module("google.cloud.firestore")
except Exception:
    firestore = None


# Global database instance
_db: Optional[firestore.Client] = None


def initialize_db() -> Optional[Any]:
    """Initialize Firestore database client.

    Returns:
        Firestore Client instance or None if not configured

    Note:
        - In Cloud Run (production): Uses default credentials
        - With Firestore emulator: Connects to emulator
        - Local development: Returns None (uses in-memory storage)
    """
    global _db

    if _db is not None:
        return _db

    try:
        # Check if running in Cloud Run (production)
        if firestore and os.environ.get('K_SERVICE'):
            _db = firestore.Client()
            print("[Database] Connected to Firestore (Cloud Run)")
            return _db

        # Check for Firestore emulator
        if firestore and os.environ.get('FIRESTORE_EMULATOR_HOST'):
            _db = firestore.Client()
            print(f"[Database] Connected to Firestore emulator: {os.environ.get('FIRESTORE_EMULATOR_HOST')}")
            return _db

        # Local development without Firestore
        print("[Database] WARNING: Firestore not configured. Using in-memory storage for development.")
        print("[Database] To use Firestore locally, set FIRESTORE_EMULATOR_HOST or run with Cloud credentials.")
        _db = None
        return None

    except Exception as e:
        print(f"[Database] WARNING: Firestore initialization failed: {e}")
        print("[Database] Using in-memory storage for development.")
        _db = None
        return None


def get_db() -> Optional[Any]:
    """Get the initialized database client.

    Returns:
        Firestore Client instance or None
    """
    if _db is None:
        return initialize_db()
    return _db
