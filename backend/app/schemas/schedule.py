from pydantic import BaseModel


class ConflictCheckRequest(BaseModel):
    activity_id: int


class AddActivityRequest(BaseModel):
    activity_id: int
    force_add: bool = False
