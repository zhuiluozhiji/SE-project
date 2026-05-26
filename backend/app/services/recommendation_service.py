from datetime import datetime, timedelta

from sqlalchemy import or_, select
from sqlalchemy.exc import OperationalError, ProgrammingError
from sqlalchemy.orm import Session

from app.models.activity import Activity
from app.models.activity_interaction import ActivityInteraction
from app.models.activity_tag import ActivityTag
from app.models.schedule_event import ScheduleEvent
from app.models.user import User
from app.models.user_interest import UserInterest
from app.services.activity_service import _activity_to_dict, _load_tags

BEHAVIOR_LOOKBACK_DAYS = 60
ACTION_WEIGHTS = {
    "view": 1.0,
    "add_schedule": 4.0,
}


def _clamp_hot_score(value: int | None) -> int:
    return max(0, min(value or 0, 100))


def _time_score(activity: Activity, now: datetime) -> int:
    if activity.start_time is None:
        return 0
    days_until_start = (activity.start_time - now).days
    if 0 <= days_until_start <= 7:
        return 15
    if 0 <= days_until_start <= 30:
        return 8
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


def _load_scheduled_activity_ids(db: Session, user_id: int | None) -> set[int]:
    if user_id is None:
        return set()
    activity_ids = db.scalars(
        select(ScheduleEvent.activity_id).where(
            ScheduleEvent.user_id == user_id,
            ScheduleEvent.type == "activity",
            ScheduleEvent.activity_id.is_not(None),
        )
    ).all()
    return set(activity_ids)


def _load_behavior_tag_weights(
    db: Session,
    user_id: int | None,
    now: datetime,
) -> dict[str, float]:
    if user_id is None:
        return {}

    cutoff = now - timedelta(days=BEHAVIOR_LOOKBACK_DAYS)
    try:
        rows = db.execute(
            select(
                ActivityTag.tag_name,
                ActivityInteraction.action_type,
                ActivityInteraction.created_at,
            )
            .join(ActivityTag, ActivityTag.activity_id == ActivityInteraction.activity_id)
            .where(
                ActivityInteraction.user_id == user_id,
                ActivityInteraction.created_at >= cutoff,
                ActivityInteraction.action_type.in_(tuple(ACTION_WEIGHTS)),
            )
        ).all()
    except (OperationalError, ProgrammingError):
        db.rollback()
        return {}

    weights: dict[str, float] = {}
    for tag_name, action_type, created_at in rows:
        action_weight = ACTION_WEIGHTS.get(action_type, 0)
        days_old = max((now - created_at).days, 0)
        decay = max(0.1, 1 - days_old / BEHAVIOR_LOOKBACK_DAYS)
        weights[tag_name] = weights.get(tag_name, 0) + action_weight * decay
    return weights


def _build_reason(
    matched_tags: list[str],
    behavior_tags: list[str],
    same_college: bool,
    hot_score: int,
    time_score: int,
    has_conflict: bool,
) -> str:
    reason_candidates: list[tuple[int, str]] = []
    if matched_tags:
        reason_candidates.append((45, "匹配兴趣标签：" + "、".join(matched_tags[:3])))
    if behavior_tags:
        reason_candidates.append((35, "最近关注过：" + "、".join(behavior_tags[:3])))
    if same_college:
        reason_candidates.append((8, "与你的学院相关"))
    if hot_score >= 10:
        reason_candidates.append((15, "活动热度较高"))
    if time_score > 0:
        reason_candidates.append((time_score, "近期开始"))
    if has_conflict:
        reason_candidates.append((40, "与已有日程存在时间冲突"))

    reasons = [reason for _, reason in sorted(reason_candidates, reverse=True)[:3]]
    if not has_conflict and len(reasons) < 3:
        reasons.append("无日程冲突")
    if not reasons:
        reasons.append("综合热度和时间推荐")
    return "；".join(reasons)


def _score_activity(
    db: Session,
    activity: Activity,
    tags: list[str],
    user: User | None,
    interest_tags: set[str],
    behavior_tag_weights: dict[str, float],
    now: datetime,
) -> dict:
    matched_tags = sorted(set(tags) & interest_tags)
    behavior_tags = sorted(
        (set(tags) & set(behavior_tag_weights)),
        key=lambda tag: (-behavior_tag_weights[tag], tag),
    )
    explicit_interest_score = min(len(matched_tags) * 20, 45)
    behavior_history_score = min(
        int(round(sum(behavior_tag_weights[tag] for tag in behavior_tags) * 10)),
        35,
    )
    hot_score = int(round(_clamp_hot_score(activity.hot_score) * 0.15))
    time_score = _time_score(activity, now)
    same_college = bool(user and user.college and user.college == activity.college)
    college_score = 8 if same_college else 0
    has_conflict = _has_time_conflict(db, user.id if user else None, activity)
    conflict_penalty = 40 if has_conflict else 0
    recommend_score = (
        explicit_interest_score
        + behavior_history_score
        + hot_score
        + time_score
        + college_score
        - conflict_penalty
    )

    return {
        "recommend_score": recommend_score,
        "reason": _build_reason(
            matched_tags=matched_tags,
            behavior_tags=behavior_tags,
            same_college=same_college,
            hot_score=hot_score,
            time_score=time_score,
            has_conflict=has_conflict,
        ),
        "matched_tags": matched_tags,
        "has_conflict": has_conflict,
        "score_breakdown": {
            "explicit_interest": explicit_interest_score,
            "behavior_history": behavior_history_score,
            "hot": hot_score,
            "time": time_score,
            "college": college_score,
            "conflict_penalty": conflict_penalty,
            "total": recommend_score,
        },
    }


def _rerank_with_category_diversity(items: list[dict]) -> list[dict]:
    remaining = items[:]
    reranked: list[dict] = []
    while remaining:
        selected_index = 0
        if len(reranked) < 10 and len(reranked) >= 2:
            previous_category = reranked[-1].get("category")
            same_category_streak = previous_category and all(
                item.get("category") == previous_category for item in reranked[-2:]
            )
            if same_category_streak:
                for index, item in enumerate(remaining):
                    if item.get("category") != previous_category:
                        selected_index = index
                        break
        reranked.append(remaining.pop(selected_index))
    return reranked


def list_recommended_activities(
    db: Session,
    limit: int,
    user_id: int | None = None,
) -> list[dict]:
    user = db.get(User, user_id) if user_id is not None else None
    interest_tags = _load_interest_tags(db, user.id if user else None)
    now = datetime.now()
    scheduled_activity_ids = _load_scheduled_activity_ids(db, user.id if user else None)
    behavior_tag_weights = _load_behavior_tag_weights(db, user.id if user else None, now)
    activities = db.scalars(
        select(Activity).where(
            Activity.status == "open",
            or_(Activity.end_time.is_(None), Activity.end_time >= now),
        )
    ).all()
    activities = [
        activity for activity in activities if activity.id not in scheduled_activity_ids
    ]
    tags_by_activity = _load_tags(db, [activity.id for activity in activities])

    items = []
    for activity in activities:
        tags = tags_by_activity.get(activity.id, [])
        scored = _score_activity(
            db=db,
            activity=activity,
            tags=tags,
            user=user,
            interest_tags=interest_tags,
            behavior_tag_weights=behavior_tag_weights,
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
    return _rerank_with_category_diversity(items)[:limit]
