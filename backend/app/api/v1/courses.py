from fastapi import APIRouter, File, UploadFile

from app.core.response import success
from app.schemas.course import CourseCreate

router = APIRouter(prefix="/courses", tags=["courses"])


@router.post("")
def create_course(payload: CourseCreate):
    return success({"id": 1, **payload.model_dump()})


@router.post("/import")
def import_courses(file: UploadFile = File(...)):
    return success({"filename": file.filename, "imported_count": 0, "status": "pending"})


@router.post("/ocr")
def ocr_course_image(file: UploadFile = File(...)):
    return success({"filename": file.filename, "courses": [], "status": "reserved"})
