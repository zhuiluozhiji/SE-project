from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.activity import Activity
from app.models.activity_interaction import ActivityInteraction
from app.models.schedule_event import ScheduleEvent
from app.models.user import User
from app.models.user_interest import UserInterest


def get_user_by_id(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)


def user_to_public(user: User) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "role": user.role,
        "major": user.major,
        "college": user.college,
    }


def user_to_profile(db: Session, user: User) -> dict:
    interests = db.scalars(
        select(UserInterest.tag_name)
        .where(UserInterest.user_id == user.id)
        .order_by(UserInterest.tag_name.asc())
    ).all()
    joined_count = (
        db.scalar(
            select(func.count(ScheduleEvent.id)).where(
                ScheduleEvent.user_id == user.id,
                ScheduleEvent.type == "activity",
            )
        )
        or 0
    )
    conflict_count = get_week_conflict_count(db, user.id)
    timeline = get_user_timeline(db, user.id)

    return {
        **user_to_public(user),
        "interests": list(interests),
        "tags": list(interests),
        "tag_count": len(interests),
        "joined_count": joined_count,
        "conflict_count": conflict_count,
        "timeline": timeline,
    }


def get_week_conflict_count(db: Session, user_id: int) -> int:
    now = datetime.now()
    week_start = now - timedelta(days=now.weekday())
    week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
    week_end = week_start + timedelta(days=7)
    events = db.execute(
        select(ScheduleEvent.id, ScheduleEvent.start_time, ScheduleEvent.end_time).where(
            ScheduleEvent.user_id == user_id,
            ScheduleEvent.start_time < week_end,
            ScheduleEvent.end_time > week_start,
        )
    ).all()
    conflict_ids: set[int] = set()
    for index, event in enumerate(events):
        for other in events[index + 1 :]:
            if event.start_time < other.end_time and event.end_time > other.start_time:
                conflict_ids.add(event.id)
                conflict_ids.add(other.id)
    return len(conflict_ids)


def get_user_timeline(db: Session, user_id: int, limit: int = 10) -> list[dict]:
    rows = db.execute(
        select(ActivityInteraction, Activity)
        .join(Activity, Activity.id == ActivityInteraction.activity_id)
        .where(ActivityInteraction.user_id == user_id)
        .order_by(ActivityInteraction.created_at.desc(), ActivityInteraction.id.desc())
        .limit(limit)
    ).all()
    return [
        {
            "id": interaction.id,
            "activity_id": activity.id,
            "title": activity.title,
            "action": action_label(interaction.action_type),
            "action_type": interaction.action_type,
            "source": interaction.source,
            "campus": activity.campus,
            "location": activity.location,
            "created_at": interaction.created_at.isoformat(),
        }
        for interaction, activity in rows
    ]


def action_label(action_type: str) -> str:
    labels = {
        "view": "浏览",
        "click": "查看",
        "favorite": "收藏",
        "join": "加入",
        "recommend_click": "查看推荐",
    }
    return labels.get(action_type, "参加")
