from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy.orm import Session

from app.core.deps import require_admin_user
from app.core.response import fail, success
from app.db.session import get_db
from app.schemas.activity import ActivityCreate, ActivityUpdate
from app.services.activity_ocr_service import ActivityOcrError, recognize_activity_images
from app.services.admin_service import create_activity as create_activity_in_db
from app.services.admin_service import get_admin_stats as get_admin_stats_from_db
from app.services.admin_service import offline_activity as offline_activity_in_db
from app.services.admin_service import update_activity as update_activity_in_db
from app.services.recommendation_service import list_recommended_activities

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(require_admin_user)],
)


@router.post("/activities")
def create_activity(payload: ActivityCreate, db: Session = Depends(get_db)):
    return success(create_activity_in_db(db, payload))


@router.put("/activities/{activity_id}")
def update_activity(activity_id: int, payload: ActivityUpdate, db: Session = Depends(get_db)):
    activity = update_activity_in_db(db, activity_id, payload)
    if activity is None:
        return fail(code=1003, message="活动不存在")
    return success(activity)


@router.delete("/activities/{activity_id}")
def offline_activity(activity_id: int, db: Session = Depends(get_db)):
    activity = offline_activity_in_db(db, activity_id)
    if activity is None:
        return fail(code=1003, message="活动不存在")
    return success(activity)


@router.post("/activities/recognize-image")
async def recognize_activity_from_image(
    files: list[UploadFile] | None = File(None),
    file: UploadFile | None = File(None),
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
        return fail(code=4001, message=str(exc))
    except ValueError as exc:
        return fail(code=4002, message=str(exc))
    return success(result)


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
