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
from app.models.schedule_event import ScheduleEvent
from app.models.user import User
from app.models.user_interest import UserInterest


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
                major="计算机科学与技术",
                college="计算机科学与技术学院",
                created_at=now,
            ),
            User(
                id=2,
                username="admin001",
                password_hash=hash_password("123456"),
                role="admin",
                college="信息技术中心",
                created_at=now,
            ),
        ]
    )
    activities = [
        Activity(
            id=101,
            title="人工智能前沿讲座",
            description="大模型和智能体。",
            college="计算机科学与技术学院",
            category="讲座",
            campus="紫金港",
            start_time=now + timedelta(days=2),
            end_time=now + timedelta(days=2, hours=2),
            source_type="manual",
            hot_score=80,
            status="open",
        ),
        Activity(
            id=102,
            title="数据库系统沙龙",
            description="查询优化和数据库内核。",
            college="软件学院",
            category="沙龙",
            campus="玉泉",
            start_time=now + timedelta(days=10),
            end_time=now + timedelta(days=10, hours=2),
            source_type="manual",
            hot_score=55,
            status="open",
        ),
        Activity(
            id=103,
            title="冲突中的机器学习工作坊",
            description="机器学习实践。",
            college="计算机科学与技术学院",
            category="工作坊",
            campus="紫金港",
            start_time=now + timedelta(days=1),
            end_time=now + timedelta(days=1, hours=2),
            source_type="manual",
            hot_score=95,
            status="open",
        ),
        Activity(
            id=104,
            title="已加入日程活动",
            description="应从登录用户推荐候选中排除。",
            college="计算机科学与技术学院",
            category="讲座",
            campus="紫金港",
            start_time=now + timedelta(days=3),
            end_time=now + timedelta(days=3, hours=2),
            source_type="manual",
            hot_score=99,
            status="open",
        ),
        Activity(
            id=105,
            title="已结束活动",
            start_time=now - timedelta(days=4),
            end_time=now - timedelta(days=3),
            hot_score=100,
            status="open",
        ),
    ]
    db.add_all(activities)
    db.add_all(
        [
            ActivityTag(activity_id=101, tag_name="人工智能"),
            ActivityTag(activity_id=102, tag_name="数据库"),
            ActivityTag(activity_id=103, tag_name="机器学习"),
            ActivityTag(activity_id=104, tag_name="人工智能"),
            UserInterest(user_id=1, tag_name="人工智能"),
            UserInterest(user_id=1, tag_name="数据库"),
            ActivityInteraction(
                user_id=1,
                activity_id=103,
                action_type="view",
                source="activity_detail",
                created_at=now,
            ),
            ScheduleEvent(
                user_id=1,
                title="已加入日程活动",
                type="activity",
                activity_id=104,
                start_time=now + timedelta(days=3),
                end_time=now + timedelta(days=3, hours=2),
                color_type="green",
            ),
            ScheduleEvent(
                user_id=1,
                title="冲突课程",
                type="course",
                start_time=now + timedelta(days=1, minutes=30),
                end_time=now + timedelta(days=1, hours=1, minutes=30),
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


def login_token(client: TestClient, username: str, password: str = "123456") -> str:
    response = client.post("/api/v1/auth/login", json={"username": username, "password": password})
    return response.json()["data"]["token"]


def assert_recommendation_shape(item: dict):
    assert "recommend_score" in item
    assert "reason" in item
    assert "matched_tags" in item
    assert "has_conflict" in item
    assert "score_breakdown" in item
    assert item["score_breakdown"]["total"] == item["recommend_score"]


def test_anonymous_recommendations_return_generic_ranked_items(client):
    response = client.get("/api/v1/recommendations/activities", params={"limit": 2})

    assert response.status_code == 200
    items = response.json()["data"]["items"]
    assert len(items) == 2
    assert all(item["status"] == "open" for item in items)
    assert 105 not in [item["id"] for item in items]
    assert all("综合" in item["reason"] or item["reason"] for item in items)
    assert_recommendation_shape(items[0])


def test_authenticated_recommendations_include_interest_behavior_and_conflict_signals(client):
    token = login_token(client, "student001")
    response = client.get(
        "/api/v1/recommendations/activities",
        params={"limit": 10},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    items = response.json()["data"]["items"]
    ids = [item["id"] for item in items]
    assert 104 not in ids

    ai_item = next(item for item in items if item["id"] == 101)
    assert "人工智能" in ai_item["matched_tags"]
    assert ai_item["score_breakdown"]["explicit_interest"] > 0
    assert ai_item["score_breakdown"]["behavior_history"] > 0
    assert "无日程冲突" not in ai_item["reason"]

    conflict_item = next(item for item in items if item["id"] == 103)
    assert conflict_item["has_conflict"] is True
    assert "最近关注过：机器学习" in conflict_item["reason"]
    assert conflict_item["score_breakdown"]["behavior_history"] > 0
    assert conflict_item["score_breakdown"]["conflict_penalty"] == 40


def test_recommendation_limit_boundary_is_validated(client):
    valid = client.get("/api/v1/recommendations/activities", params={"limit": 1})
    assert valid.status_code == 200
    assert len(valid.json()["data"]["items"]) == 1

    invalid = client.get("/api/v1/recommendations/activities", params={"limit": 0})
    assert invalid.status_code == 422


def test_admin_recommendation_preview_requires_admin_and_supports_user_id(client):
    student_token = login_token(client, "student001")
    forbidden = client.get(
        "/api/v1/admin/recommendations/preview",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert forbidden.status_code == 403

    admin_token = login_token(client, "admin001")
    response = client.get(
        "/api/v1/admin/recommendations/preview",
        params={"user_id": 1, "limit": 2},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    items = response.json()["data"]["items"]
    assert len(items) == 2
    assert_recommendation_shape(items[0])
