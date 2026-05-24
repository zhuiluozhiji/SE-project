from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.response import fail, success
from app.db.session import get_db
from app.schemas.auth import LoginRequest, RegisterRequest
from app.services.auth_service import authenticate_user, create_student_user
from app.services.user_service import user_to_public

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    auth_result = authenticate_user(db, payload.username, payload.password)
    if auth_result is None:
        return fail(code=1001, message="用户名或密码错误")
    token, user = auth_result
    return success({"token": token, "user": user_to_public(user)})


@router.post("/register")
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    register_result = create_student_user(
        db=db,
        username=payload.username,
        password=payload.password,
        major=payload.major,
        college=payload.college,
    )
    if register_result is None:
        return fail(code=1004, message="用户名已存在")
    token, user = register_result
    return success({"token": token, "user": user_to_public(user)})
