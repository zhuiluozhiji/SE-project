from fastapi import APIRouter

from app.core.response import success
from app.schemas.user import UserPublic

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me")
def get_current_user():
    user = UserPublic(
        id=1,
        username="student001",
        role="student",
        major="计算机科学与技术",
        college="计算机科学与技术学院",
    )
    return success(user.model_dump())
