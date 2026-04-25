from app.services.activity_service import list_activities_mock


def list_recommendations_mock(limit: int) -> list[dict]:
    items = list_activities_mock()[:limit]
    for item in items:
        item["reason"] = "与你的兴趣标签匹配"
    return items
