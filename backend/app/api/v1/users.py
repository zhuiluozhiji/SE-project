from fastapi import APIRouter, Depends

from app.core.deps import get_current_user as get_current_user_dependency
from app.core.response import success
from app.models.user import User
from app.services.user_service import user_to_public

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me")
def get_current_user(current_user: User = Depends(get_current_user_dependency)):
    return success(user_to_public(current_user))
