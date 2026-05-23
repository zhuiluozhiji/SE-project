from sqlalchemy import Select, and_, func, or_, select
from sqlalchemy.orm import Session

from app.models.activity import Activity
from app.models.activity_tag import ActivityTag


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


def list_activities(
    db: Session,
    keyword: str | None = None,
    category: str | None = None,
    campus: str | None = None,
    college: str | None = None,
    tag: str | None = None,
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
    )
    total = db.scalar(select(func.count()).select_from(base_stmt.subquery())) or 0

    if sort_by == "hot":
        base_stmt = base_stmt.order_by(Activity.hot_score.desc(), Activity.start_time.asc())
    else:
        base_stmt = base_stmt.order_by(Activity.start_time.asc(), Activity.id.asc())

    activities = db.scalars(base_stmt.offset((page - 1) * page_size).limit(page_size)).all()
    tags_by_activity = _load_tags(db, [activity.id for activity in activities])
    return {
        "items": [
            _activity_to_dict(activity, tags_by_activity.get(activity.id, []))
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
