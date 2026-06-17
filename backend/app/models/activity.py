from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Activity(Base):
    __tablename__ = "activity"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    speaker: Mapped[str | None] = mapped_column(String(128))
    organizer: Mapped[str | None] = mapped_column(String(128))
    college: Mapped[str | None] = mapped_column(String(128))
    category: Mapped[str | None] = mapped_column(String(64))
    campus: Mapped[str | None] = mapped_column(String(64))
    location: Mapped[str | None] = mapped_column(String(255))
    start_time: Mapped[datetime | None] = mapped_column(DateTime)
    end_time: Mapped[datetime | None] = mapped_column(DateTime)
    source_url: Mapped[str | None] = mapped_column(String(512))
    source_type: Mapped[str] = mapped_column(String(32), nullable=False, default="manual")
    hot_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="open")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
