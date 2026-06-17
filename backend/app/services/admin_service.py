from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.activity import Activity
from app.models.activity_tag import ActivityTag
from app.schemas.activity import ActivityCreate, ActivityUpdate
from app.models.user import User


def activity_to_admin_dict(activity: Activity) -> dict:
    return {
        "id": activity.id,
        "title": activity.title,
        "description": activity.description,
        "speaker": activity.speaker,
        "organizer": activity.organizer,
        "college": activity.college,
        "category": activity.category,
        "campus": activity.campus,
        "location": activity.location,
        "start_time": activity.start_time.isoformat() if activity.start_time else None,
        "end_time": activity.end_time.isoformat() if activity.end_time else None,
        "source_url": activity.source_url,
        "source_type": activity.source_type,
        "hot_score": activity.hot_score,
        "status": activity.status,
    }


def create_activity(db: Session, payload: ActivityCreate) -> dict:
    activity = Activity(
        **payload.model_dump(),
        source_type="manual",
        hot_score=0,
        status="open",
    )
    db.add(activity)
    db.commit()
    db.refresh(activity)
    return activity_to_admin_dict(activity)


def update_activity(db: Session, activity_id: int, payload: ActivityUpdate) -> dict | None:
    activity = db.get(Activity, activity_id)
    if activity is None:
        return None
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(activity, field, value)
    activity.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(activity)
    return activity_to_admin_dict(activity)


def offline_activity(db: Session, activity_id: int) -> dict | None:
    activity = db.get(Activity, activity_id)
    if activity is None:
        return None
    activity.status = "offline"
    activity.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(activity)
    return activity_to_admin_dict(activity)


def get_admin_stats(db: Session) -> dict:
    total_activities = db.scalar(select(func.count(Activity.id))) or 0
    open_activities = (
        db.scalar(select(func.count(Activity.id)).where(Activity.status == "open")) or 0
    )
    offline_activities = (
        db.scalar(select(func.count(Activity.id)).where(Activity.status == "offline")) or 0
    )
    user_count = db.scalar(select(func.count(User.id))) or 0
    tag_count = db.scalar(select(func.count(func.distinct(ActivityTag.tag_name)))) or 0
    campus_count = (
        db.scalar(
            select(func.count(func.distinct(Activity.campus))).where(
                Activity.campus.is_not(None),
                Activity.campus != "",
            )
        )
        or 0
    )
    category_count = (
        db.scalar(
            select(func.count(func.distinct(Activity.category))).where(
                Activity.category.is_not(None),
                Activity.category != "",
            )
        )
        or 0
    )
    average_hot_score = db.scalar(select(func.avg(Activity.hot_score))) or 0
    max_hot_score = db.scalar(select(func.max(Activity.hot_score))) or 0

    return {
        "activity_count": total_activities,
        "open_activity_count": open_activities,
        "offline_activity_count": offline_activities,
        "user_count": user_count,
        "tag_count": tag_count,
        "campus_count": campus_count,
        "category_count": category_count,
        "average_hot_score": round(float(average_hot_score), 2),
        "max_hot_score": max_hot_score,
    }
