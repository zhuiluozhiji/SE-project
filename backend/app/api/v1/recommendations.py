from fastapi import APIRouter, Depends, Query
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.response import success
from app.core.security import bearer_scheme, decode_access_token
from app.db.session import get_db
from app.services.recommendation_service import list_recommended_activities

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


def _optional_user_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> int | None:
    if credentials is None or credentials.scheme.lower() != "bearer":
        return None
    try:
        payload = decode_access_token(credentials.credentials)
        subject = payload.get("sub")
        return int(subject) if subject is not None else None
    except Exception:
        return None


@router.get("/activities")
def get_recommended_activities(
    limit: int = Query(10, ge=1, le=50),
    user_id: int | None = Depends(_optional_user_id),
    db: Session = Depends(get_db),
):
    return success({"items": list_recommended_activities(db=db, limit=limit, user_id=user_id)})
