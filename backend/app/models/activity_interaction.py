from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ActivityInteraction(Base):
    __tablename__ = "activity_interaction"
    __table_args__ = (
        Index("idx_activity_interaction_user_time", "user_id", "created_at"),
        Index("idx_activity_interaction_user_activity", "user_id", "activity_id"),
        Index("idx_activity_interaction_activity_action", "activity_id", "action_type"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False
    )
    activity_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("activity.id", ondelete="CASCADE"), nullable=False
    )
    action_type: Mapped[str] = mapped_column(String(32), nullable=False)
    source: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
