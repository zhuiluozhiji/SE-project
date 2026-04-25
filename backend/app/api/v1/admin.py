from fastapi import APIRouter

from app.core.response import success
from app.schemas.activity import ActivityCreate, ActivityUpdate

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/activities")
def create_activity(payload: ActivityCreate):
    return success({"id": 101, **payload.model_dump()})


@router.put("/activities/{activity_id}")
def update_activity(activity_id: int, payload: ActivityUpdate):
    return success({"id": activity_id, **payload.model_dump(exclude_none=True)})


@router.delete("/activities/{activity_id}")
def offline_activity(activity_id: int):
    return success({"id": activity_id, "status": "offline"})


@router.get("/stats")
def get_admin_stats():
    return success({"activity_count": 0, "crawler_success_count": 0, "user_count": 0})
