def list_schedule_events_mock() -> list[dict]:
    return [
        {
            "id": 1,
            "title": "机器学习课程",
            "type": "course",
            "start_time": "2026-05-10T13:00:00",
            "end_time": "2026-05-10T15:00:00",
            "location": "紫金港东1A-101",
            "status": "normal",
            "color_type": "course",
        }
    ]


def check_conflict_mock(activity_id: int) -> dict:
    return {
        "activity_id": activity_id,
        "has_conflict": True,
        "conflicts": list_schedule_events_mock(),
    }
