def list_activities_mock() -> list[dict]:
    return [
        {
            "id": 101,
            "title": "人工智能前沿讲座",
            "speaker": "张三教授",
            "start_time": "2026-05-10T14:00:00",
            "end_time": "2026-05-10T16:00:00",
            "location": "紫金港校区西区报告厅",
            "campus": "紫金港",
            "category": "讲座",
            "tags": ["人工智能", "计算机"],
            "hot_score": 87,
            "recommend_score": 92,
            "status": "open",
        }
    ]


def get_activity_mock(activity_id: int) -> dict:
    activity = list_activities_mock()[0]
    activity["id"] = activity_id
    activity["description"] = "这里后续接入数据库中的活动详情。"
    return activity
