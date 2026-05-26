from datetime import datetime

from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.response import fail, success
from app.db.session import get_db
from app.schemas.course import CourseCreate
from app.services.course_service import build_course_template_example
from app.services.course_service import create_course as create_course_service
from app.services.course_service import delete_course as delete_course_service
from app.services.course_service import import_courses_from_upload, serialize_course
from app.services.course_service import list_courses as list_courses_service

router = APIRouter(prefix="/courses", tags=["courses"])


@router.get("")
def get_courses(db: Session = Depends(get_db)):
    return success({"items": list_courses_service(db)})


@router.post("")
def create_course(payload: CourseCreate, db: Session = Depends(get_db)):
    try:
        course = create_course_service(db, payload)
    except ValueError as exc:
        return fail(code=2001, message=str(exc))
    except IntegrityError:
        db.rollback()
        return fail(code=2003, message="课程保存失败，请确认测试用户已初始化后重试。")
    return success(serialize_course(course))


@router.get("/template")
def get_course_template():
    return success(build_course_template_example())


@router.post("/import")
def import_courses(file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        result = import_courses_from_upload(
            db,
            filename=file.filename or "courses.csv",
            content=file.file.read(),
        )
    except ValueError as exc:
        return fail(code=2002, message=str(exc))
    except IntegrityError:
        db.rollback()
        return fail(code=2003, message="课表保存失败，请确认测试用户已初始化后重试。")
    return success(result)


@router.post("/ocr")
def ocr_course_image(file: UploadFile = File(...)):
    return success(
        {
            "filename": file.filename,
            "courses": [],
            "status": "reserved",
            "message": "课表截图 OCR 接口已预留，第一阶段请使用 CSV/XLSX 导入。",
        }
    )


@router.delete("/{course_id}")
def delete_course(
    course_id: int,
    scope: str = Query(
        "one",
        description="删除范围：one=仅删除本次，day=删除当天这门课，all=删除全部这门课",
    ),
    occurrence_start: datetime | None = Query(
        None,
        description="scope=one 时可传当前课程实例开始时间，仅移除这一周的这一次课程",
    ),
    db: Session = Depends(get_db),
):
    try:
        result = delete_course_service(
            db,
            course_id,
            scope=scope,
            occurrence_start=occurrence_start,
        )
    except ValueError as exc:
        return fail(code=2004, message=str(exc))
    return success(result)
