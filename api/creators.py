from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any

from auth import UserInfo, get_current_user
from db import CreatorDB


class CreatorPayload(BaseModel):
    name: str
    platform: str
    category: str
    email: str | None = None
    profile_url: str | None = None
    metadata: Dict[str, Any] | None = None


class SaveCreatorsRequest(BaseModel):
    session_id: str
    creators: List[CreatorPayload]


def build_creators_router(creator_db: CreatorDB) -> APIRouter:
    router = APIRouter()

    @router.post("/api/creators")
    def save_creators(payload: SaveCreatorsRequest, current_user: UserInfo = Depends(get_current_user)):
        if not creator_db:
            raise HTTPException(status_code=503, detail="Creator storage unavailable")
        creator_db.save_creators(
            [c.dict() for c in payload.creators],
            session_id=payload.session_id,
            user_id=current_user.user_id,
        )
        return {"status": "success", "count": len(payload.creators)}

    @router.get("/api/creators")
    def get_creators(session_id: str):
        if not creator_db:
            raise HTTPException(status_code=503, detail="Creator storage unavailable")
        creators = creator_db.get_creators_by_session(session_id)
        return {"creators": creators}

    return router
