from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class CourseSchedule(Base):
    __tablename__ = "course_schedule"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True
    )
    course_name: Mapped[str] = mapped_column(String(128), nullable=False)
    teacher: Mapped[str | None] = mapped_column(String(128))
    weekday: Mapped[int] = mapped_column(Integer, nullable=False)
    start_section: Mapped[int] = mapped_column(Integer, nullable=False)
    end_section: Mapped[int] = mapped_column(Integer, nullable=False)
    weeks: Mapped[str | None] = mapped_column(String(64))
    location: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
