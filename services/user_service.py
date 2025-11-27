"""User and identity linking helpers for Firestore."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

try:
    from google.cloud import firestore  # type: ignore
except Exception:  # pragma: no cover - firestore optional in local dev
    firestore = None


class UserService:
    """Manage user records and anon→auth linking."""

    def __init__(self, db):
        self.db = db
        self.users_collection = db.collection("users") if db else None
        self.links_collection = db.collection("user_links") if db else None

    # User records -----------------------------------------------------
    def get_user_by_creo_id(self, creo_user_id: str) -> Optional[dict]:
        if not self.users_collection:
            return None
        docs = (
            self.users_collection.where("creo_user_id", "==", creo_user_id).limit(1).stream()
        )
        for doc in docs:
            data = doc.to_dict()
            data["id"] = doc.id
            return data
        return None

    def ensure_user_record(
        self,
        creo_user_id: str,
        email: str,
        name: str,
        picture: Optional[str] = None,
    ) -> str:
        """Upsert user record; returns Firestore doc id (not the creo_user_id)."""
        if not self.users_collection:
            return ""

        existing = self.get_user_by_creo_id(creo_user_id)
        if existing:
            doc_ref = self.users_collection.document(existing["id"])
            doc_ref.set(
                {
                    "last_login_at": firestore.SERVER_TIMESTAMP if firestore else datetime.utcnow(),
                    "picture": picture,
                    "name": name,
                },
                merge=True,
            )
            return existing["id"]

        doc_ref = self.users_collection.document()
        doc_ref.set(
            {
                "creo_user_id": creo_user_id,
                "email": email,
                "name": name,
                "picture": picture,
                "created_at": firestore.SERVER_TIMESTAMP if firestore else datetime.utcnow(),
                "last_login_at": firestore.SERVER_TIMESTAMP if firestore else datetime.utcnow(),
            }
        )
        return doc_ref.id

    # Anon link management ---------------------------------------------
    def get_linked_user_id(self, anon_user_id: str) -> Optional[str]:
        """Return the creo_user_id linked to this anon id, if any."""
        if not self.links_collection:
            return None
        docs = (
            self.links_collection.where("anon_user_id", "==", anon_user_id).limit(1).stream()
        )
        for doc in docs:
            data = doc.to_dict()
            return data.get("user_id")
        return None

    def link_anon_to_user(self, anon_user_id: str, user_id: str) -> None:
        """Persist anon→user mapping."""
        if not self.links_collection:
            return

        existing_user = self.get_linked_user_id(anon_user_id)
        if existing_user and existing_user != user_id:
            raise ValueError(
                f"Anonymous ID {anon_user_id} already linked to a different user."
            )

        doc_ref = self.links_collection.document()
        doc_ref.set(
            {
                "anon_user_id": anon_user_id,
                "user_id": user_id,
                "migrated_at": firestore.SERVER_TIMESTAMP if firestore else datetime.utcnow(),
            }
        )
