from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.response import fail, success
from app.db.session import get_db
from app.schemas.auth import LoginRequest
from app.services.auth_service import authenticate_user
from app.services.user_service import user_to_public

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    auth_result = authenticate_user(db, payload.username, payload.password)
    if auth_result is None:
        return fail(code=1001, message="用户名或密码错误")
    token, user = auth_result
    return success({"token": token, "user": user_to_public(user)})
