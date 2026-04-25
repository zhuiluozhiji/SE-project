from fastapi import APIRouter

from app.core.response import success
from app.schemas.schedule import AddActivityRequest, ConflictCheckRequest
from app.services.schedule_service import check_conflict_mock, list_schedule_events_mock

router = APIRouter(prefix="/schedules", tags=["schedules"])


@router.get("")
def get_schedules(start_date: str | None = None, end_date: str | None = None):
    return success(
        {
            "items": list_schedule_events_mock(),
            "start_date": start_date,
            "end_date": end_date,
        }
    )


@router.post("/check-conflict")
def check_conflict(payload: ConflictCheckRequest):
    return success(check_conflict_mock(payload.activity_id))


@router.post("/add-activity")
def add_activity(payload: AddActivityRequest):
    return success(
        {
            "schedule_id": 2001,
            "activity_id": payload.activity_id,
            "has_conflict": False,
            "force_add": payload.force_add,
        }
    )


@router.get("/export-ics")
def export_ics():
    return success({"download_url": "/api/v1/schedules/export-ics/file"})
