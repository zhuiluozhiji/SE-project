from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.response import fail
from app.core.security import get_token_payload
from app.db.session import get_db
from app.models.user import User
from app.services.user_service import get_user_by_id


def get_current_user(
    token_payload: dict = Depends(get_token_payload),
    db: Session = Depends(get_db),
) -> User:
    user_id = token_payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=fail(code=401, message="未登录或登录已过期"),
        )
    user = get_user_by_id(db, int(user_id))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=fail(code=1002, message="用户不存在"),
        )
    return user


def require_admin_user(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=fail(code=403, message="需要管理员权限"),
        )
    return current_user
