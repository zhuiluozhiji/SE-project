from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User


def authenticate_user(db: Session, username: str, password: str) -> tuple[str, User] | None:
    user = db.scalar(select(User).where(User.username == username))
    if user is None or not verify_password(password, user.password_hash):
        return None
    token = create_access_token(subject=str(user.id), extra={"role": user.role})
    return token, user


def create_student_user(
    db: Session,
    username: str,
    password: str,
    major: str | None = None,
    college: str | None = None,
) -> tuple[str, User] | None:
    existing_user = db.scalar(select(User).where(User.username == username))
    if existing_user is not None:
        return None

    user = User(
        username=username,
        password_hash=hash_password(password),
        role="student",
        major=major,
        college=college,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token(subject=str(user.id), extra={"role": user.role})
    return token, user
