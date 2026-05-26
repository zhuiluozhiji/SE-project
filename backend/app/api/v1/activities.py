from datetime import datetime

from fastapi import APIRouter, Depends, Query
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.response import fail, success
from app.core.security import bearer_scheme, decode_access_token
from app.db.session import get_db
from app.schemas.activity import ActivityInteractionCreate
from app.services.activity_service import get_filter_options
from app.services.activity_service import get_activity as get_activity_by_id
from app.services.activity_service import list_activities as list_activities_from_db
from app.services.activity_service import record_activity_interaction

router = APIRouter(prefix="/activities", tags=["activities"])


def _optional_user_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> int | None:
    if credentials is None or credentials.scheme.lower() != "bearer":
        return None
    try:
        payload = decode_access_token(credentials.credentials)
        subject = payload.get("sub")
        return int(subject) if subject is not None else None
    except Exception:
        return None


@router.get("")
def list_activities(
    keyword: str | None = None,
    category: str | None = None,
    campus: str | None = None,
    college: str | None = None,
    tag: str | None = None,
    start_from: datetime | None = None,
    start_to: datetime | None = None,
    sort_by: str = Query("time", pattern="^(time|hot|recommend)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    result = list_activities_from_db(
        db=db,
        keyword=keyword,
        category=category,
        campus=campus,
        college=college,
        tag=tag,
        start_from=start_from,
        start_to=start_to,
        sort_by=sort_by,
        page=page,
        page_size=page_size,
    )
    result["filters"] = {
        "keyword": keyword,
        "category": category,
        "campus": campus,
        "college": college,
        "tag": tag,
        "start_from": start_from.isoformat() if start_from else None,
        "start_to": start_to.isoformat() if start_to else None,
        "sort_by": sort_by,
    }
    return success(result)


@router.get("/filter-options")
def list_filter_options(db: Session = Depends(get_db)):
    return success(get_filter_options(db))


@router.get("/{activity_id}")
def get_activity(activity_id: int, db: Session = Depends(get_db)):
    activity = get_activity_by_id(db, activity_id)
    if activity is None:
        return fail(code=1003, message="活动不存在")
    return success(activity)


@router.post("/{activity_id}/interactions")
def create_activity_interaction(
    activity_id: int,
    payload: ActivityInteractionCreate,
    user_id: int | None = Depends(_optional_user_id),
    db: Session = Depends(get_db),
):
    result = record_activity_interaction(
        db=db,
        activity_id=activity_id,
        payload=payload,
        user_id=user_id,
    )
    if result is None:
        return fail(code=1003, message="活动不存在")
    return success(result)
