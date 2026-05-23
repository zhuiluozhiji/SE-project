def list_recommendations_mock(limit: int) -> list[dict]:
    items = [
        {
            "id": 101,
            "title": "人工智能前沿讲座",
            "speaker": "张三教授",
            "start_time": "2026-05-10T14:00:00",
            "end_time": "2026-05-10T16:00:00",
            "location": "紫金港校区西区报告厅",
            "campus": "紫金港",
            "category": "讲座",
            "tags": ["人工智能", "计算机", "机器学习"],
            "hot_score": 87,
            "recommend_score": 92,
            "status": "open",
            "reason": "与你的兴趣标签匹配",
        }
    ]
    return items[:limit]
