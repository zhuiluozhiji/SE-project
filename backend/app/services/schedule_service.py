from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from icalendar import Calendar, Event
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.activity import Activity
from app.models.course_schedule import CourseSchedule
from app.models.schedule_event import ScheduleEvent
from app.utils.time import overlaps
from app.services.course_service import course_event_title_candidates, section_range_to_datetime

DEFAULT_USER_ID = 1
LOCAL_TZ = ZoneInfo("Asia/Shanghai")


def list_schedule_events(
    db: Session,
    start_date: str | None = None,
    end_date: str | None = None,
    user_id: int = DEFAULT_USER_ID,
) -> list[dict]:
    stmt = select(ScheduleEvent).where(ScheduleEvent.user_id == user_id)

    start_dt = parse_boundary(start_date)
    end_dt = parse_boundary(end_date, is_end=True)
    if start_dt:
        stmt = stmt.where(ScheduleEvent.end_time >= start_dt)
    if end_dt:
        stmt = stmt.where(ScheduleEvent.start_time <= end_dt)

    stmt = stmt.order_by(ScheduleEvent.start_time.asc(), ScheduleEvent.id.asc())
    events = db.scalars(stmt).all()
    course_id_map = build_course_id_map(db, user_id)
    return [
        serialize_event(
            event,
            course_id=course_id_map.get(course_event_key(event)),
            title=display_event_title(event),
        )
        for event in events
    ]


def check_activity_conflict(
    db: Session,
    activity_id: int,
    user_id: int = DEFAULT_USER_ID,
) -> dict:
    activity = db.get(Activity, activity_id)
    if not activity:
        raise ValueError("活动不存在")
    if not activity.start_time or not activity.end_time:
        raise ValueError("活动缺少起止时间，无法检测冲突")
    if activity.start_time >= activity.end_time:
        raise ValueError("活动时间范围无效")

    candidate = activity_to_event_dict(activity)
    conflicts = find_conflicting_events(
        db,
        user_id=user_id,
        start_time=activity.start_time,
        end_time=activity.end_time,
        exclude_activity_id=activity.id,
    )
    return {
        "activity_id": activity_id,
        "has_conflict": len(conflicts) > 0,
        "activity": candidate,
        "conflicts": [serialize_event(event, status="conflict") for event in conflicts],
    }


def add_activity_to_schedule(
    db: Session,
    activity_id: int,
    force_add: bool = False,
    user_id: int = DEFAULT_USER_ID,
) -> dict:
    conflict_result = check_activity_conflict(db, activity_id=activity_id, user_id=user_id)
    if conflict_result["has_conflict"] and not force_add:
        raise ValueError("活动与现有日程冲突，请确认后再加入")

    existing = db.scalar(
        select(ScheduleEvent).where(
            ScheduleEvent.user_id == user_id,
            ScheduleEvent.activity_id == activity_id,
            ScheduleEvent.type == "activity",
        )
    )
    if existing:
        return {
            "schedule_id": existing.id,
            "activity_id": activity_id,
            "already_exists": True,
            "has_conflict": conflict_result["has_conflict"],
            "force_add": force_add,
            "conflicts": conflict_result["conflicts"],
        }

    activity = db.get(Activity, activity_id)
    if not activity or not activity.start_time or not activity.end_time:
        raise ValueError("活动不存在或时间信息不完整")

    event = ScheduleEvent(
        user_id=user_id,
        title=activity.title,
        type="activity",
        activity_id=activity.id,
        start_time=activity.start_time,
        end_time=activity.end_time,
        location=activity.location,
        color_type="conflict" if conflict_result["has_conflict"] else "activity",
    )
    db.add(event)
    db.commit()
    db.refresh(event)

    return {
        "schedule_id": event.id,
        "activity_id": activity_id,
        "already_exists": False,
        "has_conflict": conflict_result["has_conflict"],
        "force_add": force_add,
        "conflicts": conflict_result["conflicts"],
    }


def export_schedule_ics(
    db: Session,
    user_id: int = DEFAULT_USER_ID,
) -> bytes:
    events = db.scalars(
        select(ScheduleEvent)
        .where(ScheduleEvent.user_id == user_id)
        .order_by(ScheduleEvent.start_time.asc(), ScheduleEvent.id.asc())
    ).all()

    calendar = Calendar()
    calendar.add("prodid", "-//Campus Academic Activity Recommender//SE Project//CN")
    calendar.add("version", "2.0")
    calendar.add("X-WR-CALNAME", "校园学术活动日程")

    for event in events:
        calendar_event = Event()
        calendar_event.add("uid", f"schedule-event-{event.id}@se-project.local")
        calendar_event.add("summary", event.title)
        calendar_event.add("dtstart", with_local_timezone(event.start_time))
        calendar_event.add("dtend", with_local_timezone(event.end_time))
        calendar_event.add("dtstamp", datetime.now(timezone.utc))
        if event.location:
            calendar_event.add("location", event.location)
        calendar_event.add("description", f"类型：{event.type}")
        calendar.add_component(calendar_event)

    return calendar.to_ical()


def find_conflicting_events(
    db: Session,
    user_id: int,
    start_time: datetime,
    end_time: datetime,
    exclude_activity_id: int | None = None,
) -> list[ScheduleEvent]:
    stmt = select(ScheduleEvent).where(
        ScheduleEvent.user_id == user_id,
        ScheduleEvent.start_time < end_time,
        ScheduleEvent.end_time > start_time,
    )
    if exclude_activity_id is not None:
        stmt = stmt.where(
            (ScheduleEvent.activity_id.is_(None))
            | (ScheduleEvent.activity_id != exclude_activity_id)
        )

    events = db.scalars(stmt.order_by(ScheduleEvent.start_time.asc())).all()
    return [
        event
        for event in events
        if overlaps(start_time, end_time, event.start_time, event.end_time)
    ]


def serialize_event(
    event: ScheduleEvent,
    status: str | None = None,
    course_id: int | None = None,
    title: str | None = None,
) -> dict:
    return {
        "id": event.id,
        "title": title or event.title,
        "type": event.type,
        "course_id": course_id if event.type == "course" else None,
        "activity_id": event.activity_id,
        "start_time": event.start_time,
        "end_time": event.end_time,
        "location": event.location,
        "status": status or event_status(event),
        "color_type": "conflict" if status == "conflict" else event.color_type,
    }


def build_course_id_map(db: Session, user_id: int) -> dict[tuple, int]:
    courses = db.scalars(select(CourseSchedule).where(CourseSchedule.user_id == user_id)).all()
    result = {}
    for course in courses:
        start_time, end_time = section_range_to_datetime(
            course.weekday,
            course.start_section,
            course.end_section,
        )
        for title in course_event_title_candidates(course.course_name):
            result[(title, start_time, end_time, course.location)] = course.id
    return result


def course_event_key(event: ScheduleEvent) -> tuple:
    return (event.title, event.start_time, event.end_time, event.location)


def display_event_title(event: ScheduleEvent) -> str:
    if event.type != "course":
        return event.title
    title = event.title.strip()
    if title.endswith("课程"):
        stripped = title[:-2].strip()
        return stripped or event.title
    return event.title


def activity_to_event_dict(activity: Activity) -> dict:
    return {
        "id": 0,
        "title": activity.title,
        "type": "activity",
        "activity_id": activity.id,
        "start_time": activity.start_time,
        "end_time": activity.end_time,
        "location": activity.location,
        "status": event_status_from_end_time(activity.end_time),
        "color_type": "activity",
    }


def event_status(event: ScheduleEvent) -> str:
    return event_status_from_end_time(event.end_time)


def event_status_from_end_time(end_time: datetime | None) -> str:
    if end_time and end_time < datetime.now():
        return "closed"
    return "open"


def parse_boundary(value: str | None, is_end: bool = False) -> datetime | None:
    if not value:
        return None
    try:
        if "T" in value:
            return datetime.fromisoformat(value)
        suffix = " 23:59:59" if is_end else " 00:00:00"
        return datetime.fromisoformat(f"{value}{suffix}")
    except ValueError as exc:
        raise ValueError("日期格式应为 YYYY-MM-DD 或 ISO datetime") from exc


def with_local_timezone(value: datetime) -> datetime:
    if value.tzinfo:
        return value.astimezone(LOCAL_TZ)
    return value.replace(tzinfo=LOCAL_TZ)
