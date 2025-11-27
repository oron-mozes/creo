from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from auth import UserInfo, get_current_user
from services.message_store import MessageStore
from services.user_service import UserService


class MigrateUserRequest(BaseModel):
    anonymous_user_id: str


def build_users_router(db, message_store: MessageStore, user_service: UserService) -> APIRouter:
    router = APIRouter()

    @router.post("/api/users/migrate")
    def migrate_anonymous_user(
        request: MigrateUserRequest,
        current_user: UserInfo = Depends(get_current_user)
    ):
        """
        Migrate anonymous user data to authenticated user.
        Requires authentication.
        """
        anon_user_id = request.anonymous_user_id
        auth_user_id = current_user.user_id

        print(f"[MIGRATION] Migrating anonymous user {anon_user_id} to authenticated user {auth_user_id}")

        try:
            if not anon_user_id:
                raise HTTPException(status_code=400, detail="anonymous_user_id is required")

            # Ensure user record exists
            user_service.ensure_user_record(
                creo_user_id=auth_user_id,
                email=current_user.email,
                name=current_user.name,
                picture=current_user.picture,
            )

            # Prevent cross-account takeover
            existing_link = user_service.get_linked_user_id(anon_user_id)
            if existing_link and existing_link != auth_user_id:
                raise HTTPException(status_code=409, detail="Anonymous ID already linked to a different user.")

            # Reassign all sessions/messages
            message_store.migrate_owner_ids(anon_user_id, auth_user_id)

            # Persist the link
            user_service.link_anon_to_user(anon_user_id, auth_user_id)

            print(f"[MIGRATION] Successfully migrated {anon_user_id} to {auth_user_id}")

            return {
                "status": "success",
                "message": f"Migrated {anon_user_id} to {auth_user_id}",
                "anonymous_user_id": anon_user_id,
                "authenticated_user_id": auth_user_id
            }

        except Exception as e:
            print(f"[MIGRATION] Error: {e}")
            raise HTTPException(status_code=500, detail=f"Migration failed: {str(e)}")

    return router
