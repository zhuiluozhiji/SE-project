from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import require_admin_user
from app.core.response import success
from app.db.session import get_db
from app.schemas.activity import ActivityCreate, ActivityUpdate
from app.services.admin_service import get_admin_stats as get_admin_stats_from_db
from app.services.recommendation_service import list_recommended_activities

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(require_admin_user)],
)


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
def get_admin_stats(db: Session = Depends(get_db)):
    return success(get_admin_stats_from_db(db))


@router.get("/recommendations/preview")
def preview_recommendations(
    user_id: int | None = None,
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    return success({"items": list_recommended_activities(db=db, limit=limit, user_id=user_id)})
