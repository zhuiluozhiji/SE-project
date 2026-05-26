from datetime import datetime

from sqlalchemy import Select, and_, func, or_, select
from sqlalchemy.exc import OperationalError, ProgrammingError
from sqlalchemy.orm import Session

from app.models.activity import Activity
from app.models.activity_interaction import ActivityInteraction
from app.models.activity_tag import ActivityTag
from app.schemas.activity import ActivityInteractionCreate

ZJU_CAMPUSES = ["紫金港", "玉泉", "西溪", "华家池", "之江", "舟山", "海宁"]


def _iso(value):
    return value.isoformat() if value else None


def _activity_to_dict(activity: Activity, tags: list[str]) -> dict:
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
        "start_time": _iso(activity.start_time),
        "end_time": _iso(activity.end_time),
        "source_url": activity.source_url,
        "source_type": activity.source_type,
        "hot_score": activity.hot_score,
        "status": activity.status,
        "tags": tags,
    }


def _apply_filters(
    stmt: Select[tuple[Activity]],
    keyword: str | None = None,
    category: str | None = None,
    campus: str | None = None,
    college: str | None = None,
    tag: str | None = None,
    start_from: datetime | None = None,
    start_to: datetime | None = None,
) -> Select[tuple[Activity]]:
    conditions = [Activity.status == "open"]
    if keyword:
        like_keyword = f"%{keyword}%"
        conditions.append(
            or_(
                Activity.title.like(like_keyword),
                Activity.description.like(like_keyword),
                Activity.speaker.like(like_keyword),
                Activity.organizer.like(like_keyword),
                Activity.location.like(like_keyword),
            )
        )
    if category:
        conditions.append(Activity.category == category)
    if campus:
        conditions.append(Activity.campus == campus)
    if college:
        conditions.append(Activity.college == college)
    if tag:
        stmt = stmt.join(ActivityTag, ActivityTag.activity_id == Activity.id)
        conditions.append(ActivityTag.tag_name == tag)
    if start_from:
        conditions.append(Activity.start_time >= start_from)
    if start_to:
        conditions.append(Activity.start_time <= start_to)
    return stmt.where(and_(*conditions))


def _load_tags(db: Session, activity_ids: list[int]) -> dict[int, list[str]]:
    if not activity_ids:
        return {}
    rows = db.execute(
        select(ActivityTag.activity_id, ActivityTag.tag_name).where(
            ActivityTag.activity_id.in_(activity_ids)
        )
    ).all()
    tags_by_activity: dict[int, list[str]] = {activity_id: [] for activity_id in activity_ids}
    for activity_id, tag_name in rows:
        tags_by_activity.setdefault(activity_id, []).append(tag_name)
    return tags_by_activity


def _generic_recommend_score(activity: Activity) -> int:
    hot_score = max(0, min(activity.hot_score or 0, 100)) * 0.3
    time_score = 0
    if activity.start_time:
        days_until_start = (activity.start_time - datetime.now()).days
        if 0 <= days_until_start <= 7:
            time_score = 20
        elif 0 <= days_until_start <= 30:
            time_score = 10
    return int(round(hot_score + time_score))


def list_activities(
    db: Session,
    keyword: str | None = None,
    category: str | None = None,
    campus: str | None = None,
    college: str | None = None,
    tag: str | None = None,
    start_from: datetime | None = None,
    start_to: datetime | None = None,
    sort_by: str = "time",
    page: int = 1,
    page_size: int = 10,
) -> dict:
    base_stmt = _apply_filters(
        select(Activity),
        keyword=keyword,
        category=category,
        campus=campus,
        college=college,
        tag=tag,
        start_from=start_from,
        start_to=start_to,
    )
    total = db.scalar(select(func.count()).select_from(base_stmt.subquery())) or 0

    if sort_by == "recommend":
        activities_all = db.scalars(base_stmt).all()
        activities_all.sort(
            key=lambda activity: (
                -_generic_recommend_score(activity),
                activity.start_time or datetime.max,
                activity.id,
            )
        )
        activities = activities_all[(page - 1) * page_size : page * page_size]
    elif sort_by == "hot":
        base_stmt = base_stmt.order_by(Activity.hot_score.desc(), Activity.start_time.asc())
        activities = db.scalars(base_stmt.offset((page - 1) * page_size).limit(page_size)).all()
    else:
        base_stmt = base_stmt.order_by(Activity.start_time.asc(), Activity.id.asc())
        activities = db.scalars(base_stmt.offset((page - 1) * page_size).limit(page_size)).all()

    tags_by_activity = _load_tags(db, [activity.id for activity in activities])
    return {
        "items": [
            {
                **_activity_to_dict(activity, tags_by_activity.get(activity.id, [])),
                **(
                    {"recommend_score": _generic_recommend_score(activity)}
                    if sort_by == "recommend"
                    else {}
                ),
            }
            for activity in activities
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


def get_activity(db: Session, activity_id: int) -> dict | None:
    activity = db.get(Activity, activity_id)
    if activity is None or activity.status != "open":
        return None
    tags_by_activity = _load_tags(db, [activity.id])
    return _activity_to_dict(activity, tags_by_activity.get(activity.id, []))


def record_activity_interaction(
    db: Session,
    activity_id: int,
    payload: ActivityInteractionCreate,
    user_id: int | None,
) -> dict | None:
    if user_id is None:
        return {
            "recorded": False,
            "reason": "anonymous_user",
            "activity_id": activity_id,
            "action_type": payload.action_type,
        }

    activity = db.get(Activity, activity_id)
    if activity is None or activity.status != "open":
        return None

    interaction = ActivityInteraction(
        user_id=user_id,
        activity_id=activity_id,
        action_type=payload.action_type,
        source=payload.source,
    )
    db.add(interaction)
    try:
        db.commit()
    except (OperationalError, ProgrammingError):
        db.rollback()
        return {
            "recorded": False,
            "reason": "interaction_storage_unavailable",
            "activity_id": activity_id,
            "action_type": payload.action_type,
        }
    db.refresh(interaction)
    return {
        "recorded": True,
        "id": interaction.id,
        "activity_id": activity_id,
        "action_type": interaction.action_type,
        "source": interaction.source,
        "created_at": interaction.created_at.isoformat(),
    }


def get_filter_options(db: Session) -> dict:
    def distinct_values(column) -> list[str]:
        rows = db.scalars(
            select(column)
            .where(Activity.status == "open", column.is_not(None), column != "")
            .distinct()
            .order_by(column.asc())
        ).all()
        return list(rows)

    tags = db.scalars(
        select(ActivityTag.tag_name)
        .join(Activity, Activity.id == ActivityTag.activity_id)
        .where(Activity.status == "open", ActivityTag.tag_name != "")
        .distinct()
        .order_by(ActivityTag.tag_name.asc())
    ).all()

    return {
        "categories": distinct_values(Activity.category),
        "campuses": list(dict.fromkeys([*ZJU_CAMPUSES, *distinct_values(Activity.campus)])),
        "colleges": distinct_values(Activity.college),
        "tags": list(tags),
    }


def list_activities_mock() -> list[dict]:
    return [
        {
            "id": 101,
            "title": "人工智能前沿讲座",
            "description": "围绕大模型、智能体和可信 AI 的前沿进展进行分享。",
            "speaker": "张三教授",
            "organizer": "计算机科学与技术学院",
            "college": "计算机科学与技术学院",
            "category": "讲座",
            "campus": "紫金港",
            "location": "紫金港校区西区报告厅",
            "start_time": "2026-05-10T14:00:00",
            "end_time": "2026-05-10T16:00:00",
            "source_url": "https://example.com/activity/101",
            "source_type": "manual",
            "hot_score": 87,
            "recommend_score": 92,
            "status": "open",
            "tags": ["人工智能", "计算机"],
        }
    ]
