from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.activity import Activity
from app.models.activity_tag import ActivityTag
from app.models.user import User


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
