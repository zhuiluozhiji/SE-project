from fastapi import APIRouter

from app.core.response import success
from app.core.security import create_access_token
from app.schemas.auth import LoginRequest
from app.schemas.user import UserPublic

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
def login(payload: LoginRequest):
    user = UserPublic(
        id=1,
        username=payload.username,
        role="student",
        major="计算机科学与技术",
        college="计算机科学与技术学院",
    )
    token = create_access_token(subject=str(user.id), extra={"role": user.role})
    return success({"token": token, "user": user.model_dump()})
