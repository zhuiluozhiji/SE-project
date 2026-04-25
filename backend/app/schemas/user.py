from pydantic import BaseModel


class UserPublic(BaseModel):
    id: int
    username: str
    role: str
    major: str | None = None
    college: str | None = None
