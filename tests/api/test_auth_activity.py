from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import hash_password
from app.db.session import get_db
from app.main import app
from app.models.base import Base
from app.models.activity import Activity
from app.models.activity_tag import ActivityTag
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
    now = datetime(2026, 5, 23, 10, 0, 0)
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
    db.add(
        User(
            id=2,
            username="admin001",
            password_hash=hash_password("123456"),
            role="admin",
            major=None,
            college="信息技术中心",
            created_at=now,
        )
    )
    db.add(
        Activity(
            id=101,
            title="人工智能前沿讲座",
            description="围绕大模型和智能体进行分享。",
            speaker="张三教授",
            organizer="计算机科学与技术学院",
            college="计算机科学与技术学院",
            category="讲座",
            campus="紫金港",
            location="紫金港校区西区报告厅",
            start_time=datetime(2026, 5, 10, 14, 0, 0),
            end_time=datetime(2026, 5, 10, 16, 0, 0),
            source_url="https://example.com/activity/101",
            source_type="manual",
            hot_score=87,
            status="open",
            created_at=now,
            updated_at=now,
        )
    )
    db.add(ActivityTag(activity_id=101, tag_name="人工智能"))
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


def test_login_and_get_current_user(client):
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "student001", "password": "123456"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0
    assert data["data"]["user"]["username"] == "student001"

    token = data["data"]["token"]
    me_response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_response.status_code == 200
    assert me_response.json()["data"]["id"] == 1


def test_register_creates_student_user(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "newstudent",
            "password": "123456",
            "major": "软件工程",
            "college": "软件学院",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0
    assert data["data"]["user"]["username"] == "newstudent"
    assert data["data"]["user"]["role"] == "student"
    assert data["data"]["token"]


def test_register_rejects_duplicate_username(client):
    response = client.post(
        "/api/v1/auth/register",
        json={"username": "student001", "password": "123456"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 1004


def test_admin_login_and_admin_permission(client):
    admin_login = client.post(
        "/api/v1/auth/login",
        json={"username": "admin001", "password": "123456"},
    )
    assert admin_login.status_code == 200
    admin_data = admin_login.json()
    assert admin_data["code"] == 0
    assert admin_data["data"]["user"]["role"] == "admin"

    student_login = client.post(
        "/api/v1/auth/login",
        json={"username": "student001", "password": "123456"},
    )
    student_token = student_login.json()["data"]["token"]
    forbidden_response = client.get(
        "/api/v1/admin/stats",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert forbidden_response.status_code == 403

    admin_token = admin_data["data"]["token"]
    stats_response = client.get(
        "/api/v1/admin/stats",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert stats_response.status_code == 200
    assert stats_response.json()["code"] == 0


def test_list_and_get_activity_from_database(client):
    list_response = client.get("/api/v1/activities", params={"page": 1, "page_size": 10})
    assert list_response.status_code == 200
    list_data = list_response.json()
    assert list_data["code"] == 0
    assert list_data["data"]["total"] == 1
    assert list_data["data"]["items"][0]["tags"] == ["人工智能"]

    detail_response = client.get("/api/v1/activities/101")
    assert detail_response.status_code == 200
    assert detail_response.json()["data"]["title"] == "人工智能前沿讲座"
