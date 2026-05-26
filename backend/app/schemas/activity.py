from datetime import datetime
from typing import Literal

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


class ActivityInteractionCreate(BaseModel):
    action_type: Literal["view", "add_schedule"]
    source: str | None = None
