from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.activity import Activity
from app.models.schedule_event import ScheduleEvent
from app.models.user import User
from app.models.user_interest import UserInterest
from app.services.activity_service import _activity_to_dict, _load_tags


def _clamp_hot_score(value: int | None) -> int:
    return max(0, min(value or 0, 100))


def _time_score(activity: Activity, now: datetime) -> int:
    if activity.start_time is None:
        return 0
    days_until_start = (activity.start_time - now).days
    if 0 <= days_until_start <= 7:
        return 20
    if 0 <= days_until_start <= 30:
        return 10
    return 0


def _has_time_conflict(db: Session, user_id: int | None, activity: Activity) -> bool:
    if user_id is None or activity.start_time is None or activity.end_time is None:
        return False
    return (
        db.scalar(
            select(ScheduleEvent.id)
            .where(
                ScheduleEvent.user_id == user_id,
                ScheduleEvent.start_time < activity.end_time,
                ScheduleEvent.end_time > activity.start_time,
            )
            .limit(1)
        )
        is not None
    )


def _load_interest_tags(db: Session, user_id: int | None) -> set[str]:
    if user_id is None:
        return set()
    tags = db.scalars(
        select(UserInterest.tag_name).where(UserInterest.user_id == user_id)
    ).all()
    return set(tags)


def _build_reason(
    matched_tags: list[str],
    same_college: bool,
    hot_score: int,
    time_score: int,
    has_conflict: bool,
) -> str:
    reasons: list[str] = []
    if matched_tags:
        reasons.append("匹配兴趣标签：" + "、".join(matched_tags))
    if same_college:
        reasons.append("与你的学院相关")
    if hot_score >= 20:
        reasons.append("活动热度较高")
    if time_score > 0:
        reasons.append("近期开始")
    if has_conflict:
        reasons.append("与已有日程存在时间冲突")
    if not reasons:
        reasons.append("综合热度和时间推荐")
    return "；".join(reasons)


def _score_activity(
    db: Session,
    activity: Activity,
    tags: list[str],
    user: User | None,
    interest_tags: set[str],
    now: datetime,
) -> dict:
    matched_tags = sorted(set(tags) & interest_tags)
    tag_score = min(len(matched_tags) * 30, 60)
    hot_score = int(round(_clamp_hot_score(activity.hot_score) * 0.3))
    time_score = _time_score(activity, now)
    same_college = bool(user and user.college and user.college == activity.college)
    college_score = 10 if same_college else 0
    has_conflict = _has_time_conflict(db, user.id if user else None, activity)
    conflict_penalty = 40 if has_conflict else 0
    recommend_score = tag_score + hot_score + time_score + college_score - conflict_penalty

    return {
        "recommend_score": recommend_score,
        "reason": _build_reason(
            matched_tags=matched_tags,
            same_college=same_college,
            hot_score=hot_score,
            time_score=time_score,
            has_conflict=has_conflict,
        ),
        "matched_tags": matched_tags,
        "has_conflict": has_conflict,
    }


def list_recommended_activities(
    db: Session,
    limit: int,
    user_id: int | None = None,
) -> list[dict]:
    user = db.get(User, user_id) if user_id is not None else None
    interest_tags = _load_interest_tags(db, user.id if user else None)
    activities = db.scalars(select(Activity).where(Activity.status == "open")).all()
    tags_by_activity = _load_tags(db, [activity.id for activity in activities])
    now = datetime.now()

    items = []
    for activity in activities:
        tags = tags_by_activity.get(activity.id, [])
        scored = _score_activity(
            db=db,
            activity=activity,
            tags=tags,
            user=user,
            interest_tags=interest_tags,
            now=now,
        )
        items.append({**_activity_to_dict(activity, tags), **scored})

    items.sort(
        key=lambda item: (
            -item["recommend_score"],
            item["start_time"] or "",
            item["id"],
        )
    )
    return items[:limit]
