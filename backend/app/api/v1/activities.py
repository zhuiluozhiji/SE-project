from fastapi import APIRouter, Query

from app.core.response import success
from app.services.activity_service import get_activity_mock, list_activities_mock

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
):
    items = list_activities_mock()
    return success(
        {
            "items": items,
            "total": len(items),
            "page": page,
            "page_size": page_size,
            "filters": {
                "keyword": keyword,
                "category": category,
                "campus": campus,
                "college": college,
                "tag": tag,
                "sort_by": sort_by,
            },
        }
    )


@router.get("/{activity_id}")
def get_activity(activity_id: int):
    return success(get_activity_mock(activity_id))
