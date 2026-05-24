from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class UserInterest(Base):
    __tablename__ = "user_interest"
    __table_args__ = (UniqueConstraint("user_id", "tag_name", name="uk_user_interest"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False
    )
    tag_name: Mapped[str] = mapped_column(String(64), nullable=False)
