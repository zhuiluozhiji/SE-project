from pydantic import BaseModel


class CourseCreate(BaseModel):
    course_name: str
    weekday: int
    start_section: int
    end_section: int
    location: str | None = None
    teacher: str | None = None
    weeks: str | None = None
