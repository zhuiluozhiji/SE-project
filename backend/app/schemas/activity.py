from datetime import datetime

from pydantic import BaseModel


class ActivityBase(BaseModel):
    title: str
    description: str | None = None
    speaker: str | None = None
    organizer: str | None = None
    college: str | None = None
    category: str | None = None
    campus: str | None = None
    location: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    source_url: str | None = None


class ActivityCreate(ActivityBase):
    pass


class ActivityUpdate(ActivityBase):
    title: str | None = None
