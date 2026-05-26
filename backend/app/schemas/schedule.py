from datetime import datetime

from pydantic import BaseModel


class ConflictCheckRequest(BaseModel):
    activity_id: int


class AddActivityRequest(BaseModel):
    activity_id: int
    force_add: bool = False


class CustomEventBase(BaseModel):
    title: str
    start_time: datetime
    end_time: datetime
    location: str | None = None
    remark: str | None = None


class CustomEventConflictCheckRequest(CustomEventBase):
    pass


class AddCustomEventRequest(CustomEventBase):
    force_add: bool = False
    color_type: str | None = None
    marker_label: str | None = None


class ScheduleAppearanceUpdate(BaseModel):
    color_type: str | None = None
    marker_label: str | None = None
    remark: str | None = None


class ScheduleEventPublic(BaseModel):
    id: int
    title: str
    type: str
    course_id: int | None = None
    teacher: str | None = None
    weeks: str | None = None
    activity_id: int | None = None
    start_time: datetime
    end_time: datetime
    location: str | None = None
    remark: str | None = None
    status: str
    color_type: str
    marker_label: str
    is_conflict: bool


class ConflictCheckResult(BaseModel):
    activity_id: int
    has_conflict: bool
    activity: ScheduleEventPublic | None = None
    conflicts: list[ScheduleEventPublic]


class AddActivityResult(BaseModel):
    schedule_id: int
    activity_id: int | None = None
    already_exists: bool = False
    has_conflict: bool
    force_add: bool
    conflicts: list[ScheduleEventPublic]
