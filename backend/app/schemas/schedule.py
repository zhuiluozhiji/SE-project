from datetime import datetime

from pydantic import BaseModel


class ConflictCheckRequest(BaseModel):
    activity_id: int


class AddActivityRequest(BaseModel):
    activity_id: int
    force_add: bool = False


class ScheduleEventPublic(BaseModel):
    id: int
    title: str
    type: str
    course_id: int | None = None
    activity_id: int | None = None
    start_time: datetime
    end_time: datetime
    location: str | None = None
    status: str
    color_type: str


class ConflictCheckResult(BaseModel):
    activity_id: int
    has_conflict: bool
    activity: ScheduleEventPublic | None = None
    conflicts: list[ScheduleEventPublic]


class AddActivityResult(BaseModel):
    schedule_id: int
    activity_id: int
    has_conflict: bool
    force_add: bool
    conflicts: list[ScheduleEventPublic]
