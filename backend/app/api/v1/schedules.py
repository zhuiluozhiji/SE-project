from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.core.response import fail, success
from app.db.session import get_db
from app.schemas.schedule import AddActivityRequest, ConflictCheckRequest
from app.services.schedule_service import (
    add_activity_to_schedule,
    check_activity_conflict,
    export_schedule_ics,
    list_schedule_events,
)

router = APIRouter(prefix="/schedules", tags=["schedules"])


@router.get("")
def get_schedules(
    start_date: str | None = None,
    end_date: str | None = None,
    db: Session = Depends(get_db),
):
    try:
        items = list_schedule_events(db, start_date=start_date, end_date=end_date)
    except ValueError as exc:
        return fail(code=3001, message=str(exc))
    return success({"items": items, "start_date": start_date, "end_date": end_date})


@router.post("/check-conflict")
def check_conflict(payload: ConflictCheckRequest, db: Session = Depends(get_db)):
    try:
        result = check_activity_conflict(db, payload.activity_id)
    except ValueError as exc:
        return fail(code=3002, message=str(exc))
    return success(result)


@router.post("/add-activity")
def add_activity(payload: AddActivityRequest, db: Session = Depends(get_db)):
    try:
        result = add_activity_to_schedule(
            db,
            activity_id=payload.activity_id,
            force_add=payload.force_add,
        )
    except ValueError as exc:
        return fail(code=3003, message=str(exc))
    return success(result)


@router.get("/export-ics")
def export_ics(db: Session = Depends(get_db)):
    items = list_schedule_events(db)
    return success(
        {
            "download_url": "/api/v1/schedules/export-ics/file",
            "event_count": len(items),
        }
    )


@router.get("/export-ics/file")
def export_ics_file(db: Session = Depends(get_db)):
    content = export_schedule_ics(db)
    return Response(
        content=content,
        media_type="text/calendar; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="schedule.ics"'},
    )
