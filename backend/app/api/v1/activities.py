from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.response import fail, success
from app.db.session import get_db
from app.services.activity_service import get_activity as get_activity_by_id
from app.services.activity_service import list_activities as list_activities_from_db

router = APIRouter(prefix="/activities", tags=["activities"])


@router.get("")
def list_activities(
    keyword: str | None = None,
    category: str | None = None,
    campus: str | None = None,
    college: str | None = None,
    tag: str | None = None,
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
        "sort_by": sort_by,
    }
    return success(result)


@router.get("/{activity_id}")
def get_activity(activity_id: int, db: Session = Depends(get_db)):
    activity = get_activity_by_id(db, activity_id)
    if activity is None:
        return fail(code=1003, message="活动不存在")
    return success(activity)
