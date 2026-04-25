from fastapi import APIRouter, Query

from app.core.response import success
from app.services.recommendation_service import list_recommendations_mock

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.get("/activities")
def get_recommended_activities(limit: int = Query(10, ge=1, le=50)):
    return success({"items": list_recommendations_mock(limit)})
