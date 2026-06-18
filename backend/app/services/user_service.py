from datetime import datetime, timedelta

from sqlalchemy import case, desc, func, select
from sqlalchemy.orm import Session

from app.models.activity import Activity
from app.models.activity_interaction import ActivityInteraction
from app.models.activity_tag import ActivityTag
from app.models.schedule_event import ScheduleEvent
from app.models.user import User
from app.models.user_interest import UserInterest

BEHAVIOR_INTEREST_LOOKBACK_DAYS = 60
BEHAVIOR_INTEREST_LIMIT = 8
PROFILE_INTEREST_MODE = "fixed_demo_users"  # 改为 "auto" 即恢复显式标签 + 行为标签的自动合并模式
FIXED_PROFILE_INTERESTS_BY_USERNAME = {
    "Mike": [
        "数据库",
        "创新",
        "智能控制",
        "人工智能",
        "计算机科学与技术学院",
        "社会实践",
    ],
    "steph": [
        "数据库",
        "创新",
        "智能控制",
        "人工智能",
        "计算机科学与技术学院",
        "社会实践",
    ],
}
PROFILE_ACTION_WEIGHTS = {
    "view": 1.0,
    "recommend_click": 2.0,
    "add_schedule": 4.0,
}


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
    explicit_interests = db.scalars(
        select(UserInterest.tag_name)
        .where(UserInterest.user_id == user.id)
        .order_by(UserInterest.tag_name.asc())
    ).all()
    if PROFILE_INTEREST_MODE == "fixed_demo_users" and user.username in FIXED_PROFILE_INTERESTS_BY_USERNAME:
        interests = FIXED_PROFILE_INTERESTS_BY_USERNAME[user.username]
        behavior_interests = []
    else:
        behavior_interests = get_behavior_interest_tags(db, user.id)
        interests = merge_interest_tags(list(explicit_interests), behavior_interests)
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
        "interests": interests,
        "tags": interests,
        "tag_count": len(interests),
        "explicit_interests": list(explicit_interests),
        "behavior_interests": behavior_interests,
        "joined_count": joined_count,
        "conflict_count": conflict_count,
        "timeline": timeline,
    }


def merge_interest_tags(explicit_interests: list[str], behavior_interests: list[str]) -> list[str]:
    merged: list[str] = []
    seen: set[str] = set()
    for tag in [*explicit_interests, *behavior_interests]:
        if tag and tag not in seen:
            merged.append(tag)
            seen.add(tag)
    return merged


def get_behavior_interest_tags(db: Session, user_id: int) -> list[str]:
    tag_interests = get_behavior_tag_interests(db, user_id)
    field_interests = get_behavior_field_interests(db, user_id)
    return merge_interest_tags(tag_interests, field_interests)


def get_behavior_tag_interests(db: Session, user_id: int) -> list[str]:
    cutoff = datetime.now() - timedelta(days=BEHAVIOR_INTEREST_LOOKBACK_DAYS)
    weighted_score = func.sum(
        case(PROFILE_ACTION_WEIGHTS, value=ActivityInteraction.action_type, else_=0)
    )
    rows = db.execute(
        select(ActivityTag.tag_name, weighted_score.label("score"))
        .join(ActivityInteraction, ActivityInteraction.activity_id == ActivityTag.activity_id)
        .where(
            ActivityInteraction.user_id == user_id,
            ActivityInteraction.created_at >= cutoff,
            ActivityInteraction.action_type.in_(tuple(PROFILE_ACTION_WEIGHTS)),
            ActivityTag.tag_name != "",
        )
        .group_by(ActivityTag.tag_name)
        .order_by(desc("score"), ActivityTag.tag_name.asc())
        .limit(BEHAVIOR_INTEREST_LIMIT)
    ).all()
    return [tag_name for tag_name, _ in rows]


def get_behavior_field_interests(db: Session, user_id: int) -> list[str]:
    cutoff = datetime.now() - timedelta(days=BEHAVIOR_INTEREST_LOOKBACK_DAYS)
    weighted_score = func.sum(
        case(PROFILE_ACTION_WEIGHTS, value=ActivityInteraction.action_type, else_=0)
    )
    rows = db.execute(
        select(Activity.college, Activity.category, weighted_score.label("score"))
        .join(Activity, Activity.id == ActivityInteraction.activity_id)
        .where(
            ActivityInteraction.user_id == user_id,
            ActivityInteraction.created_at >= cutoff,
            ActivityInteraction.action_type.in_(tuple(PROFILE_ACTION_WEIGHTS)),
        )
        .group_by(Activity.college, Activity.category)
        .order_by(desc("score"), Activity.college.asc(), Activity.category.asc())
        .limit(BEHAVIOR_INTEREST_LIMIT)
    ).all()

    interests: list[str] = []
    for college, category, _ in rows:
        if college:
            interests.append(college)
        if category and category != "其他":
            interests.append(category)
    return merge_interest_tags([], interests)[:BEHAVIOR_INTEREST_LIMIT]


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
