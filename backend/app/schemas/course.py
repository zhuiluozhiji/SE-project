from pydantic import BaseModel


class CourseCreate(BaseModel):
    course_name: str
    weekday: int
    start_section: int
    end_section: int
    location: str | None = None
    teacher: str | None = None
    weeks: str | None = None


class CoursePublic(CourseCreate):
    id: int


class CourseImportResult(BaseModel):
    filename: str
    imported_count: int
    skipped_count: int
    courses: list[CoursePublic]
    errors: list[str] = []
