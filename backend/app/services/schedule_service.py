import re
from datetime import date, datetime, timezone, timedelta
from zoneinfo import ZoneInfo

from icalendar import Calendar, Event
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.activity import Activity
from app.models.course_schedule import CourseSchedule
from app.models.schedule_event import ScheduleEvent
from app.utils.time import overlaps
from app.services.course_service import (
    COURSE_TITLE_SUFFIX,
    SECTION_TIMES,
    course_event_title,
    course_event_title_candidates,
)

DEFAULT_USER_ID = 1
LOCAL_TZ = ZoneInfo("Asia/Shanghai")
SEMESTER_WEEK_ONE_MONDAY = date(2026, 3, 2)
DEFAULT_SEMESTER_WEEKS = 20
SCHEDULE_COLOR_TYPES = {
    "blue",
    "green",
    "teal",
    "amber",
    "orange",
    "red",
    "purple",
    "pink",
    "gray",
}
LEGACY_COLOR_MAP = {
    "course": "blue",
    "activity": "green",
    "recommended": "amber",
    "conflict": "red",
    "exam": "purple",
}
DEFAULT_COLOR_BY_TYPE = {
    "course": "blue",
    "activity": "green",
    "exam": "purple",
}
DEFAULT_MARKER_BY_TYPE = {
    "course": "课",
    "activity": "活",
    "exam": "考",
}


def list_schedule_events(
    db: Session,
    start_date: str | None = None,
    end_date: str | None = None,
    user_id: int = DEFAULT_USER_ID,
) -> list[dict]:
    stmt = select(ScheduleEvent).where(ScheduleEvent.user_id == user_id)

    start_dt = parse_boundary(start_date)
    end_dt = parse_boundary(end_date, is_end=True)
    request_monday = requested_week_monday(start_dt, end_dt)
    if start_dt:
        stmt = stmt.where(ScheduleEvent.end_time >= start_dt)
    if end_dt:
        stmt = stmt.where(ScheduleEvent.start_time <= end_dt)

    stmt = stmt.order_by(ScheduleEvent.start_time.asc(), ScheduleEvent.id.asc())
    events = db.scalars(stmt).all()
    course_lookup = build_course_lookup(db, user_id)
    course_template_lookup = build_course_template_lookup(db, user_id, course_lookup)
    expanded_courses = build_course_events_for_week(db, user_id, request_monday, course_template_lookup)
    display_events = filter_template_course_events(events, course_template_lookup) + expanded_courses
    display_events.sort(key=lambda event: (event.start_time, event.id))
    conflict_ids = build_conflict_ids(display_events)
    return [
        serialize_event(
            event,
            course=resolve_course_for_event(course_lookup, event),
            title=display_event_title(event),
            is_conflict=event.id in conflict_ids,
        )
        for event in display_events
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
    course_lookup = build_course_lookup(db, user_id)
    return {
        "activity_id": activity_id,
        "has_conflict": len(conflicts) > 0,
        "activity": candidate,
        "conflicts": [serialize_conflict_event(event, course_lookup) for event in conflicts],
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
        color_type="red" if conflict_result["has_conflict"] else "green",
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


def check_custom_event_conflict(
    db: Session,
    title: str,
    start_time: datetime,
    end_time: datetime,
    location: str | None = None,
    remark: str | None = None,
    user_id: int = DEFAULT_USER_ID,
    exclude_event_id: int | None = None,
) -> dict:
    title = normalize_custom_event_title(title)
    start_time = normalize_schedule_datetime(start_time)
    end_time = normalize_schedule_datetime(end_time)
    remark = normalize_remark(remark)
    validate_custom_event_time(start_time, end_time)

    conflicts = find_conflicting_events(
        db,
        user_id=user_id,
        start_time=start_time,
        end_time=end_time,
        exclude_event_id=exclude_event_id,
    )
    course_lookup = build_course_lookup(db, user_id)
    return {
        "has_conflict": len(conflicts) > 0,
        "event": custom_event_dict(
            title=title,
            start_time=start_time,
            end_time=end_time,
            location=location,
            remark=remark,
        ),
        "conflicts": [serialize_conflict_event(event, course_lookup) for event in conflicts],
    }


def add_custom_event_to_schedule(
    db: Session,
    title: str,
    start_time: datetime,
    end_time: datetime,
    location: str | None = None,
    remark: str | None = None,
    force_add: bool = False,
    color_type: str | None = None,
    marker_label: str | None = None,
    user_id: int = DEFAULT_USER_ID,
) -> dict:
    title = normalize_custom_event_title(title)
    start_time = normalize_schedule_datetime(start_time)
    end_time = normalize_schedule_datetime(end_time)
    normalized_remark = normalize_remark(remark)
    validate_custom_event_time(start_time, end_time)

    existing = db.scalar(
        select(ScheduleEvent).where(
            ScheduleEvent.user_id == user_id,
            ScheduleEvent.type == "activity",
            ScheduleEvent.activity_id.is_(None),
            ScheduleEvent.title == title,
            ScheduleEvent.start_time == start_time,
            ScheduleEvent.end_time == end_time,
        )
    )
    if existing:
        conflict_result = check_custom_event_conflict(
            db,
            title=title,
            start_time=start_time,
            end_time=end_time,
            location=location,
            remark=normalized_remark,
            user_id=user_id,
            exclude_event_id=existing.id,
        )
        if color_type is not None:
            existing.color_type = normalize_color_type(color_type, existing.type)
        if marker_label is not None:
            normalized_marker = marker_label.strip()
            if len(normalized_marker) != 1:
                raise ValueError("单字标识必须且只能填写一个字")
            existing.marker_label = normalized_marker
        if remark is not None:
            existing.remark = normalized_remark
        db.commit()
        db.refresh(existing)
        return {
            "schedule_id": existing.id,
            "activity_id": None,
            "already_exists": True,
            "has_conflict": conflict_result["has_conflict"],
            "force_add": force_add,
            "conflicts": conflict_result["conflicts"],
            "event": serialize_event(existing, is_conflict=conflict_result["has_conflict"]),
        }

    conflict_result = check_custom_event_conflict(
        db,
        title=title,
        start_time=start_time,
        end_time=end_time,
        location=location,
        remark=normalized_remark,
        user_id=user_id,
    )
    if conflict_result["has_conflict"] and not force_add:
        raise ValueError("活动与现有日程冲突，请确认后再加入")

    normalized_color = normalize_color_type(
        color_type or ("red" if conflict_result["has_conflict"] else "green"),
        "activity",
    )
    normalized_marker = (marker_label or default_marker_for_type("activity")).strip()
    if len(normalized_marker) != 1:
        raise ValueError("单字标识必须且只能填写一个字")

    event = ScheduleEvent(
        user_id=user_id,
        title=title,
        type="activity",
        activity_id=None,
        start_time=start_time,
        end_time=end_time,
        location=location,
        color_type=normalized_color,
        marker_label=normalized_marker,
        remark=normalized_remark,
    )
    db.add(event)
    db.commit()
    db.refresh(event)

    return {
        "schedule_id": event.id,
        "activity_id": None,
        "already_exists": False,
        "has_conflict": conflict_result["has_conflict"],
        "force_add": force_add,
        "conflicts": conflict_result["conflicts"],
        "event": serialize_event(event, is_conflict=conflict_result["has_conflict"]),
    }


def delete_schedule_event(
    db: Session,
    event_id: int,
    user_id: int = DEFAULT_USER_ID,
) -> dict:
    event = db.get(ScheduleEvent, event_id)
    if not event or event.user_id != user_id:
        raise ValueError("日程不存在")
    if event.type == "course":
        raise ValueError("课程日程请通过课程删除操作移除")

    result = {
        "id": event.id,
        "title": event.title,
        "type": event.type,
        "activity_id": event.activity_id,
    }
    db.delete(event)
    db.commit()
    return result


def update_schedule_event_appearance(
    db: Session,
    event_id: int,
    color_type: str | None = None,
    marker_label: str | None = None,
    remark: str | None = None,
    update_remark: bool = False,
    user_id: int = DEFAULT_USER_ID,
) -> dict:
    event = db.get(ScheduleEvent, event_id)
    if not event or event.user_id != user_id:
        raise ValueError("日程不存在")

    if color_type is not None:
        normalized_color = normalize_color_type(color_type, event.type)
        if normalized_color not in SCHEDULE_COLOR_TYPES:
            raise ValueError("颜色标识无效，请选择可用颜色")
        event.color_type = normalized_color

    if marker_label is not None:
        normalized_marker = marker_label.strip()
        if len(normalized_marker) != 1:
            raise ValueError("单字标识必须且只能填写一个字")
        event.marker_label = normalized_marker

    if update_remark:
        event.remark = normalize_remark(remark)

    db.commit()
    db.refresh(event)
    return serialize_event(event)


def export_schedule_ics(
    db: Session,
    user_id: int = DEFAULT_USER_ID,
) -> bytes:
    events = list_schedule_events(db, user_id=user_id)

    calendar = Calendar()
    calendar.add("prodid", "-//Campus Academic Activity Recommender//SE Project//CN")
    calendar.add("version", "2.0")
    calendar.add("X-WR-CALNAME", "校园学术活动日程")

    for event in events:
        calendar_event = Event()
        start_time = event["start_time"]
        end_time = event["end_time"]
        calendar_event.add("uid", f"schedule-event-{event['id']}-{start_time:%Y%m%d%H%M}@se-project.local")
        calendar_event.add("summary", event["title"])
        calendar_event.add("dtstart", with_local_timezone(start_time))
        calendar_event.add("dtend", with_local_timezone(end_time))
        calendar_event.add("dtstamp", datetime.now(timezone.utc))
        if event["location"]:
            calendar_event.add("location", event["location"])
        description_lines = [f"类型：{event['type']}"]
        if event.get("remark"):
            description_lines.append(f"备注：{event['remark']}")
        calendar_event.add("description", "\n".join(description_lines))
        calendar.add_component(calendar_event)

    return calendar.to_ical()


def find_conflicting_events(
    db: Session,
    user_id: int,
    start_time: datetime,
    end_time: datetime,
    exclude_activity_id: int | None = None,
    exclude_event_id: int | None = None,
) -> list[ScheduleEvent]:
    course_lookup = build_course_lookup(db, user_id)
    course_template_lookup = build_course_template_lookup(db, user_id, course_lookup)
    week_monday = requested_week_monday(start_time, end_time)
    expanded_courses = build_course_events_for_week(db, user_id, week_monday, course_template_lookup)

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
    if exclude_event_id is not None:
        stmt = stmt.where(ScheduleEvent.id != exclude_event_id)

    events = db.scalars(stmt.order_by(ScheduleEvent.start_time.asc())).all()
    events = filter_template_course_events(events, course_template_lookup) + expanded_courses
    return [
        event
        for event in sorted(events, key=lambda item: (item.start_time, item.id))
        if overlaps(start_time, end_time, event.start_time, event.end_time)
        and event.id != exclude_event_id
    ]


def build_conflict_ids(events: list[ScheduleEvent]) -> set[int]:
    conflict_ids: set[int] = set()
    for index, event in enumerate(events):
        for other in events[index + 1 :]:
            if overlaps(event.start_time, event.end_time, other.start_time, other.end_time):
                conflict_ids.add(event.id)
                conflict_ids.add(other.id)
    return conflict_ids


def serialize_event(
    event: ScheduleEvent,
    status: str | None = None,
    course: dict | None = None,
    title: str | None = None,
    is_conflict: bool = False,
) -> dict:
    return {
        "id": event.id,
        "title": title or event.title,
        "type": event.type,
        "course_id": course["id"] if event.type == "course" and course else None,
        "teacher": course["teacher"] if event.type == "course" and course else None,
        "weeks": course["weeks"] if event.type == "course" and course else None,
        "activity_id": event.activity_id,
        "start_time": event.start_time,
        "end_time": event.end_time,
        "location": event.location,
        "remark": event.remark,
        "status": status or event_status(event),
        "color_type": normalize_color_type(event.color_type, event.type),
        "marker_label": event.marker_label or default_marker_for_type(event.type),
        "is_conflict": is_conflict or status == "conflict",
    }


def serialize_conflict_event(
    event: ScheduleEvent,
    course_lookup: dict[str, dict[tuple, dict | None]],
) -> dict:
    return serialize_event(
        event,
        status="conflict",
        course=resolve_course_for_event(course_lookup, event),
        title=display_event_title(event),
        is_conflict=True,
    )


def normalize_color_type(value: str | None, event_type: str | None = None) -> str:
    if not value:
        return DEFAULT_COLOR_BY_TYPE.get(event_type or "", "gray")
    normalized = value.strip().lower()
    if normalized in SCHEDULE_COLOR_TYPES:
        return normalized
    if normalized in LEGACY_COLOR_MAP:
        return LEGACY_COLOR_MAP[normalized]
    return DEFAULT_COLOR_BY_TYPE.get(event_type or "", "gray")


def default_marker_for_type(event_type: str | None) -> str:
    return DEFAULT_MARKER_BY_TYPE.get(event_type or "", "日")


def requested_week_monday(start_dt: datetime | None, end_dt: datetime | None) -> date:
    base = start_dt or end_dt or datetime.now()
    base_date = normalize_schedule_datetime(base).date()
    return base_date - timedelta(days=base_date.weekday())


def build_course_lookup(db: Session, user_id: int) -> dict[str, dict[tuple, dict | None]]:
    courses = db.scalars(select(CourseSchedule).where(CourseSchedule.user_id == user_id)).all()
    exact: dict[tuple, dict] = {}
    loose: dict[tuple, dict | None] = {}
    for course in courses:
        metadata = {
            "id": course.id,
            "teacher": course.teacher,
            "weeks": course.weeks,
        }
        for title in course_event_title_candidates(course.course_name):
            exact[(title, course.weekday, course.start_section, course.end_section, course.location)] = metadata
            loose_key = (strip_course_title_suffix(title), course.location)
            if loose_key in loose and loose[loose_key] and loose[loose_key]["id"] != course.id:
                loose[loose_key] = None
            else:
                loose[loose_key] = metadata
    return {"exact": exact, "loose": loose}


def build_course_template_lookup(
    db: Session,
    user_id: int,
    course_lookup: dict[str, dict[tuple, dict | None]],
) -> dict[int, ScheduleEvent]:
    events = db.scalars(
        select(ScheduleEvent).where(
            ScheduleEvent.user_id == user_id,
            ScheduleEvent.type == "course",
        )
    ).all()
    result: dict[int, ScheduleEvent] = {}
    for event in events:
        course = resolve_course_for_event(course_lookup, event)
        if course:
            result.setdefault(course["id"], event)
    return result


def build_course_events_for_week(
    db: Session,
    user_id: int,
    week_monday: date,
    template_lookup: dict[int, ScheduleEvent],
) -> list[ScheduleEvent]:
    week_number = semester_week_number(week_monday)
    courses = db.scalars(
        select(CourseSchedule)
        .where(CourseSchedule.user_id == user_id)
        .order_by(CourseSchedule.weekday.asc(), CourseSchedule.start_section.asc(), CourseSchedule.id.asc())
    ).all()
    events = []
    for course in courses:
        if not course_occurs_in_week(course.weeks, week_number):
            continue
        template = template_lookup.get(course.id)
        events.append(course_to_week_event(course, week_monday, template))
    return events


def course_to_week_event(
    course: CourseSchedule,
    week_monday: date,
    template: ScheduleEvent | None = None,
) -> ScheduleEvent:
    start_time, end_time = course_datetime_for_week(
        week_monday,
        course.weekday,
        course.start_section,
        course.end_section,
    )
    event = ScheduleEvent(
        id=template.id if template else -course.id,
        user_id=course.user_id,
        title=course_event_title(course.course_name),
        type="course",
        activity_id=None,
        start_time=start_time,
        end_time=end_time,
        location=course.location,
        color_type=template.color_type if template else "blue",
        marker_label=template.marker_label if template else None,
        remark=template.remark if template else None,
    )
    return event


def course_datetime_for_week(
    week_monday: date,
    weekday: int,
    start_section: int,
    end_section: int,
) -> tuple[datetime, datetime]:
    target_date = week_monday + timedelta(days=weekday - 1)
    start_clock = SECTION_TIMES.get(start_section, SECTION_TIMES[1])[0]
    end_clock = SECTION_TIMES.get(end_section, SECTION_TIMES[13])[1]
    return datetime.combine(target_date, start_clock), datetime.combine(target_date, end_clock)


def semester_week_number(week_monday: date) -> int:
    return ((week_monday - SEMESTER_WEEK_ONE_MONDAY).days // 7) + 1


def course_occurs_in_week(weeks: str | None, week_number: int) -> bool:
    if week_number < 1:
        return False
    text = (weeks or "").strip()
    if not text:
        return week_number <= DEFAULT_SEMESTER_WEEKS
    if "单周" in text and week_number % 2 == 0:
        return False
    if "双周" in text and week_number % 2 == 1:
        return False

    ranges = parse_week_ranges(text)
    if not ranges:
        return week_number <= DEFAULT_SEMESTER_WEEKS
    return any(start <= week_number <= end for start, end in ranges)


def parse_week_ranges(text: str) -> list[tuple[int, int]]:
    ranges: list[tuple[int, int]] = []
    normalized = text.replace("，", ",").replace("、", ",")
    for match in re.finditer(r"(?<!\d)(\d{1,2})(?:\s*(?:-|~|—|–|至)\s*(\d{1,2}))?", normalized):
        start = int(match.group(1))
        end = int(match.group(2) or start)
        if start <= 0:
            continue
        if end < start:
            start, end = end, start
        ranges.append((start, end))
    return ranges


def filter_template_course_events(
    stored_events: list[ScheduleEvent],
    template_lookup: dict[int, ScheduleEvent],
) -> list[ScheduleEvent]:
    template_ids = {event.id for event in template_lookup.values()}
    return [
        event
        for event in stored_events
        if event.type != "course" or event.id not in template_ids
    ]


def resolve_course_for_event(
    course_lookup: dict[str, dict[tuple, dict | None]],
    event: ScheduleEvent,
) -> dict | None:
    if event.type != "course":
        return None

    section_range = section_range_from_event(event)
    if section_range:
        exact_key = (
            event.title,
            event.start_time.isoweekday(),
            section_range[0],
            section_range[1],
            event.location,
        )
        course = course_lookup["exact"].get(exact_key)
        if course:
            return course

    loose_key = (strip_course_title_suffix(event.title), event.location)
    return course_lookup["loose"].get(loose_key)


def section_range_from_event(event: ScheduleEvent) -> tuple[int, int] | None:
    start_clock = event.start_time.time().replace(second=0, microsecond=0)
    end_clock = event.end_time.time().replace(second=0, microsecond=0)
    start_section = next((section for section, times in SECTION_TIMES.items() if times[0] == start_clock), None)
    end_section = next((section for section, times in SECTION_TIMES.items() if times[1] == end_clock), None)
    if start_section is None or end_section is None:
        return None
    return start_section, end_section


def strip_course_title_suffix(title: str) -> str:
    stripped = title.strip()
    while stripped.endswith(COURSE_TITLE_SUFFIX):
        stripped = stripped[: -len(COURSE_TITLE_SUFFIX)].strip()
    return stripped or title.strip()


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
        "remark": None,
        "status": event_status_from_end_time(activity.end_time),
        "color_type": "green",
        "marker_label": default_marker_for_type("activity"),
        "is_conflict": False,
    }


def custom_event_dict(
    title: str,
    start_time: datetime,
    end_time: datetime,
    location: str | None = None,
    remark: str | None = None,
) -> dict:
    return {
        "id": 0,
        "title": title,
        "type": "activity",
        "activity_id": None,
        "start_time": start_time,
        "end_time": end_time,
        "location": location,
        "remark": remark,
        "status": event_status_from_end_time(end_time),
        "color_type": "green",
        "marker_label": default_marker_for_type("activity"),
        "is_conflict": False,
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


def normalize_schedule_datetime(value: datetime) -> datetime:
    if value.tzinfo:
        return value.astimezone(LOCAL_TZ).replace(tzinfo=None)
    return value.replace(tzinfo=None)


def normalize_custom_event_title(title: str) -> str:
    normalized = (title or "").strip()
    if not normalized:
        raise ValueError("请输入活动名称")
    if len(normalized) > 255:
        raise ValueError("活动名称过长，请控制在 255 字以内")
    return normalized


def normalize_remark(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    if not normalized:
        return None
    if len(normalized) > 500:
        raise ValueError("备注过长，请控制在 500 字以内")
    return normalized


def validate_custom_event_time(start_time: datetime, end_time: datetime):
    if start_time >= end_time:
        raise ValueError("活动结束时间必须晚于开始时间")


def with_local_timezone(value: datetime) -> datetime:
    if value.tzinfo:
        return value.astimezone(LOCAL_TZ)
    return value.replace(tzinfo=LOCAL_TZ)
