from datetime import datetime

from fastapi import APIRouter, Depends, File, Response, UploadFile
from sqlalchemy.orm import Session

from app.core.response import fail, success
from app.db.session import get_db
from app.schemas.schedule import (
    AddActivityRequest,
    AddCustomEventRequest,
    ConflictCheckRequest,
    CustomEventConflictCheckRequest,
    ScheduleAppearanceUpdate,
)
from app.services.activity_ocr_service import ActivityOcrError, recognize_activity_images
from app.services.schedule_service import (
    add_activity_to_schedule,
    add_custom_event_to_schedule,
    check_activity_conflict,
    check_custom_event_conflict,
    delete_schedule_event,
    export_schedule_ics,
    list_schedule_events,
    update_schedule_event_appearance,
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


@router.post("/check-custom-event")
def check_custom_event(payload: CustomEventConflictCheckRequest, db: Session = Depends(get_db)):
    try:
        result = check_custom_event_conflict(
            db,
            title=payload.title,
            start_time=payload.start_time,
            end_time=payload.end_time,
            location=payload.location,
            remark=payload.remark,
        )
    except ValueError as exc:
        return fail(code=3006, message=str(exc))
    return success(result)


@router.post("/add-custom-event")
def add_custom_event(payload: AddCustomEventRequest, db: Session = Depends(get_db)):
    try:
        result = add_custom_event_to_schedule(
            db,
            title=payload.title,
            start_time=payload.start_time,
            end_time=payload.end_time,
            location=payload.location,
            remark=payload.remark,
            force_add=payload.force_add,
            color_type=payload.color_type,
            marker_label=payload.marker_label,
        )
    except ValueError as exc:
        return fail(code=3007, message=str(exc))
    return success(result)


@router.post("/recognize-image")
async def recognize_schedule_image(
    files: list[UploadFile] | None = File(None),
    file: UploadFile | None = File(None),
    db: Session = Depends(get_db),
):
    try:
        uploads = files or ([file] if file else [])
        result = recognize_activity_images(
            [
                (upload.filename or f"activity-{index + 1}.png", await upload.read())
                for index, upload in enumerate(uploads)
            ]
        )
    except ActivityOcrError as exc:
        return fail(code=3008, message=str(exc))
    except ValueError as exc:
        return fail(code=3009, message=str(exc))

    result.update(build_recognized_schedule_preview(db, result.get("activity") or {}))
    return success(result)


@router.delete("/{event_id}")
def delete_event(event_id: int, db: Session = Depends(get_db)):
    try:
        result = delete_schedule_event(db, event_id=event_id)
    except ValueError as exc:
        return fail(code=3004, message=str(exc))
    return success(result)


@router.patch("/{event_id}/appearance")
def update_event_appearance(
    event_id: int,
    payload: ScheduleAppearanceUpdate,
    db: Session = Depends(get_db),
):
    try:
        result = update_schedule_event_appearance(
            db,
            event_id=event_id,
            color_type=payload.color_type,
            marker_label=payload.marker_label,
            remark=payload.remark,
            update_remark="remark" in payload.model_fields_set,
        )
    except ValueError as exc:
        return fail(code=3005, message=str(exc))
    return success(result)


@router.patch("/{event_id}/color")
def update_event_color(
    event_id: int,
    payload: ScheduleAppearanceUpdate,
    db: Session = Depends(get_db),
):
    return update_event_appearance(event_id=event_id, payload=payload, db=db)


@router.get("/export-ics")
def export_ics(db: Session = Depends(get_db)):
    items = list_schedule_events(db)
    return success(
        {
            "download_url": "/api/v1/schedules/export-ics/file",
            "event_count": len(items),
        }
    )


def build_recognized_schedule_preview(db: Session, activity: dict) -> dict:
    event = {
        "title": activity.get("title") or "",
        "type": "activity",
        "activity_id": None,
        "start_time": activity.get("start_time"),
        "end_time": activity.get("end_time"),
        "location": activity.get("location"),
        "remark": activity.get("remark"),
        "color_type": "green",
        "marker_label": "活",
        "is_conflict": False,
    }
    preview = {"event": event, "has_conflict": False, "conflicts": []}
    if not event["title"] or not event["start_time"] or not event["end_time"]:
        return preview

    try:
        conflict = check_custom_event_conflict(
            db,
            title=event["title"],
            start_time=datetime.fromisoformat(event["start_time"]),
            end_time=datetime.fromisoformat(event["end_time"]),
            location=event["location"],
        )
    except ValueError:
        return preview

    event["is_conflict"] = conflict["has_conflict"]
    event["color_type"] = "red" if conflict["has_conflict"] else "green"
    preview["has_conflict"] = conflict["has_conflict"]
    preview["conflicts"] = conflict["conflicts"]
    return preview


@router.get("/export-ics/file")
def export_ics_file(db: Session = Depends(get_db)):
    content = export_schedule_ics(db)
    return Response(
        content=content,
        media_type="text/calendar; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="schedule.ics"'},
    )
