from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import create_access_token, verify_password
from app.models.user import User


def authenticate_user(db: Session, username: str, password: str) -> tuple[str, User] | None:
    user = db.scalar(select(User).where(User.username == username))
    if user is None or not verify_password(password, user.password_hash):
        return None
    token = create_access_token(subject=str(user.id), extra={"role": user.role})
    return token, user
