from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.response import fail, success
from app.core.security import get_token_payload
from app.db.session import get_db
from app.services.user_service import get_user_by_id, user_to_public

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me")
def get_current_user(
    token_payload: dict = Depends(get_token_payload),
    db: Session = Depends(get_db),
):
    user_id = token_payload.get("sub")
    if user_id is None:
        return fail(code=401, message="未登录或登录已过期")
    user = get_user_by_id(db, int(user_id))
    if user is None:
        return fail(code=1002, message="用户不存在")
    return success(user_to_public(user))
