from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import hash_password
from app.db.session import get_db
from app.main import app
from app.models.activity import Activity
from app.models.activity_interaction import ActivityInteraction
from app.models.activity_tag import ActivityTag
from app.models.base import Base
from app.models.user import User


@pytest.fixture()
def client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()
    now = datetime.now().replace(microsecond=0)
    db.add(
        User(
            id=1,
            username="student001",
            password_hash=hash_password("123456"),
            role="student",
            major="计算机科学与技术",
            college="计算机科学与技术学院",
            created_at=now,
        )
    )
    db.add_all(
        [
            Activity(
                id=101,
                title="人工智能前沿讲座",
                description="围绕大模型和可信 AI 的分享。",
                speaker="张三教授",
                organizer="计算机科学与技术学院",
                college="计算机科学与技术学院",
                category="讲座",
                campus="紫金港",
                location="西区报告厅",
                start_time=now + timedelta(days=2),
                end_time=now + timedelta(days=2, hours=2),
                source_url="https://example.com/ai",
                source_type="manual",
                hot_score=90,
                status="open",
            ),
            Activity(
                id=102,
                title="数据库系统沙龙",
                description="数据库内核与查询优化。",
                speaker="李四研究员",
                organizer="软件学院",
                college="软件学院",
                category="沙龙",
                campus="玉泉",
                location="曹楼会议室",
                start_time=now + timedelta(days=5),
                end_time=now + timedelta(days=5, hours=2),
                source_url="https://example.com/db",
                source_type="manual",
                hot_score=60,
                status="open",
            ),
            Activity(
                id=103,
                title="已下架活动",
                category="讲座",
                campus="紫金港",
                status="offline",
            ),
        ]
    )
    db.add_all(
        [
            ActivityTag(activity_id=101, tag_name="人工智能"),
            ActivityTag(activity_id=101, tag_name="机器学习"),
            ActivityTag(activity_id=102, tag_name="数据库"),
        ]
    )
    db.commit()
    db.close()

    def override_get_db():
        testing_db = TestingSessionLocal()
        try:
            yield testing_db
        finally:
            testing_db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def login_token(client: TestClient) -> str:
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "student001", "password": "123456"},
    )
    return response.json()["data"]["token"]


def test_filter_options_return_open_activity_values(client):
    response = client.get("/api/v1/activities/filter-options")

    assert response.status_code == 200
    data = response.json()["data"]
    assert "讲座" in data["categories"]
    assert "沙龙" in data["categories"]
    assert "紫金港" in data["campuses"]
    assert "玉泉" in data["campuses"]
    assert "计算机科学与技术学院" in data["colleges"]
    assert "人工智能" in data["tags"]
    assert "数据库" in data["tags"]


def test_activity_keyword_category_campus_and_tag_filters(client):
    keyword_response = client.get("/api/v1/activities", params={"keyword": "数据库"})
    keyword_items = keyword_response.json()["data"]["items"]
    assert [item["id"] for item in keyword_items] == [102]

    filtered_response = client.get(
        "/api/v1/activities",
        params={"category": "讲座", "campus": "紫金港", "tag": "人工智能"},
    )
    filtered = filtered_response.json()["data"]
    assert filtered["total"] == 1
    assert filtered["items"][0]["id"] == 101
    assert filtered["items"][0]["tags"] == ["人工智能", "机器学习"]


def test_activity_no_result_and_invalid_query_boundaries(client):
    empty_response = client.get("/api/v1/activities", params={"keyword": "不存在的主题"})
    assert empty_response.status_code == 200
    assert empty_response.json()["data"]["total"] == 0

    missing_detail = client.get("/api/v1/activities/999")
    assert missing_detail.status_code == 200
    assert missing_detail.json()["code"] == 1003

    invalid_sort = client.get("/api/v1/activities", params={"sort_by": "unknown"})
    assert invalid_sort.status_code == 422

    invalid_page = client.get("/api/v1/activities", params={"page": 0})
    assert invalid_page.status_code == 422


def test_anonymous_activity_interaction_is_skipped_but_successful(client):
    response = client.post(
        "/api/v1/activities/101/interactions",
        json={"action_type": "view", "source": "activity_detail"},
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["recorded"] is False
    assert data["reason"] == "anonymous_user"


def test_authenticated_activity_interaction_is_persisted(client):
    token = login_token(client)
    response = client.post(
        "/api/v1/activities/101/interactions",
        headers={"Authorization": f"Bearer {token}"},
        json={"action_type": "add_schedule", "source": "activity_detail"},
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["recorded"] is True
    assert data["activity_id"] == 101
    assert data["action_type"] == "add_schedule"


def test_interaction_for_missing_activity_returns_business_error(client):
    token = login_token(client)
    response = client.post(
        "/api/v1/activities/999/interactions",
        headers={"Authorization": f"Bearer {token}"},
        json={"action_type": "view", "source": "activity_detail"},
    )

    assert response.status_code == 200
    assert response.json()["code"] == 1003
