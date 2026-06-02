from datetime import datetime, timedelta
from time import perf_counter

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import hash_password
from app.db.session import get_db
from app.main import app
from app.models.activity import Activity
from app.models.activity_tag import ActivityTag
from app.models.base import Base
from app.models.schedule_event import ScheduleEvent
from app.models.user import User
from app.models.user_interest import UserInterest


REPEAT_COUNT = 8


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
    db.add_all(
        [
            User(
                id=1,
                username="student001",
                password_hash=hash_password("123456"),
                role="student",
                college="计算机科学与技术学院",
                created_at=now,
            ),
            User(
                id=2,
                username="admin001",
                password_hash=hash_password("123456"),
                role="admin",
                created_at=now,
            ),
            Activity(
                id=101,
                title="人工智能前沿讲座",
                description="稳定性测试活动",
                college="计算机科学与技术学院",
                category="讲座",
                campus="紫金港",
                start_time=now + timedelta(days=2),
                end_time=now + timedelta(days=2, hours=2),
                hot_score=88,
                status="open",
            ),
            ActivityTag(activity_id=101, tag_name="人工智能"),
            UserInterest(user_id=1, tag_name="人工智能"),
            ScheduleEvent(
                user_id=1,
                title="机器学习课程",
                type="course",
                start_time=now + timedelta(days=1),
                end_time=now + timedelta(days=1, hours=2),
                color_type="blue",
            ),
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


def login_token(client: TestClient, username: str) -> str:
    response = client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": "123456"},
    )
    assert response.status_code == 200
    assert response.json()["code"] == 0
    return response.json()["data"]["token"]


def repeated_get(client: TestClient, url: str, *, headers: dict | None = None) -> float:
    start = perf_counter()
    for _ in range(REPEAT_COUNT):
        response = client.get(url, headers=headers or {})
        assert response.status_code == 200
        body = response.json() if response.headers.get("content-type", "").startswith("application/json") else None
        if body is not None:
            assert body["code"] == 0
    return perf_counter() - start


def test_repeated_login_activity_and_recommendation_requests_are_stable(client):
    for _ in range(REPEAT_COUNT):
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "student001", "password": "123456"},
        )
        assert response.status_code == 200
        assert response.json()["code"] == 0

    elapsed = repeated_get(client, "/api/v1/activities?page=1&page_size=10")
    assert elapsed < 5

    token = login_token(client, "student001")
    elapsed = repeated_get(
        client,
        "/api/v1/recommendations/activities?limit=5",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert elapsed < 5


def test_repeated_schedule_ics_and_admin_stats_requests_are_stable(client):
    elapsed = repeated_get(client, "/api/v1/schedules")
    assert elapsed < 5

    for _ in range(REPEAT_COUNT):
        response = client.get("/api/v1/schedules/export-ics/file")
        assert response.status_code == 200
        assert "BEGIN:VCALENDAR" in response.text
    admin_token = login_token(client, "admin001")
    elapsed = repeated_get(
        client,
        "/api/v1/admin/stats",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert elapsed < 5
