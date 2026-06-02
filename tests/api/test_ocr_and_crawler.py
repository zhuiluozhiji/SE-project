from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.api.v1.admin as admin_api
import app.api.v1.crawler as crawler_api
import app.api.v1.schedules as schedules_api
from app.core.security import hash_password
from app.db.session import get_db
from app.main import app
from app.models.base import Base
from app.models.crawl_record import CrawlRecord
from app.models.schedule_event import ScheduleEvent
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
    db.add_all(
        [
            User(
                id=1,
                username="student001",
                password_hash=hash_password("123456"),
                role="student",
                created_at=now,
            ),
            User(
                id=2,
                username="admin001",
                password_hash=hash_password("123456"),
                role="admin",
                created_at=now,
            ),
            ScheduleEvent(
                user_id=1,
                title="机器学习课程",
                type="course",
                start_time=now + timedelta(days=1, hours=1),
                end_time=now + timedelta(days=1, hours=3),
                location="东1A-101",
                color_type="blue",
            ),
            CrawlRecord(
                source="cs_zju",
                status="success",
                fetched_count=10,
                success_count=3,
                error_msg="filtered=2",
                run_time=now,
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
    return response.json()["data"]["token"]


def recognized_payload(start: str, end: str) -> dict:
    return {
        "text": "活动标题：AI 讲座\n时间：2026-06-02 10:00-12:00",
        "warnings": [],
        "activity": {
            "title": "AI 讲座",
            "start_time": start,
            "end_time": end,
            "location": "紫金港西区",
            "remark": "OCR 导入",
        },
    }


def test_admin_activity_ocr_endpoint_uses_recognizer(monkeypatch, client):
    def fake_recognizer(files):
        assert files[0][0] == "poster.png"
        return recognized_payload("2026-06-02T10:00:00", "2026-06-02T12:00:00")

    monkeypatch.setattr(admin_api, "recognize_activity_images", fake_recognizer)
    token = login_token(client, "admin001")
    response = client.post(
        "/api/v1/admin/activities/recognize-image",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("poster.png", b"fake-image", "image/png")},
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["activity"]["title"] == "AI 讲座"
    assert data["activity"]["location"] == "紫金港西区"


def test_admin_activity_ocr_requires_admin_role(monkeypatch, client):
    monkeypatch.setattr(
        admin_api,
        "recognize_activity_images",
        lambda files: recognized_payload("2026-06-02T10:00:00", "2026-06-02T12:00:00"),
    )
    token = login_token(client, "student001")
    response = client.post(
        "/api/v1/admin/activities/recognize-image",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("poster.png", b"fake-image", "image/png")},
    )

    assert response.status_code == 403


def test_schedule_ocr_endpoint_returns_conflict_preview(monkeypatch, client):
    start = (datetime.now().replace(microsecond=0) + timedelta(days=1, hours=1, minutes=30))
    end = start + timedelta(hours=1)
    monkeypatch.setattr(
        schedules_api,
        "recognize_activity_images",
        lambda files: recognized_payload(start.isoformat(), end.isoformat()),
    )

    response = client.post(
        "/api/v1/schedules/recognize-image",
        files={"file": ("schedule.png", b"fake-image", "image/png")},
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["activity"]["title"] == "AI 讲座"
    assert data["event"]["title"] == "AI 讲座"
    assert data["has_conflict"] is True
    assert data["event"]["color_type"] == "red"
    assert data["conflicts"]


def test_ocr_endpoint_reports_missing_file(client):
    token = login_token(client, "admin001")
    response = client.post(
        "/api/v1/admin/activities/recognize-image",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["code"] == 4002


def test_crawler_run_endpoint_can_be_exercised_without_network(monkeypatch, client):
    def fake_run(db, source="cs_zju"):
        return {
            "status": "success",
            "fetched": 12,
            "created": 4,
            "skipped": 3,
            "filtered": 2,
            "year_filtered": 3,
        }

    monkeypatch.setattr(crawler_api, "run_crawler_and_save", fake_run)
    response = client.post("/api/v1/admin/crawler/run", json={"source": "cs_zju"})

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["source"] == "cs_zju"
    assert data["status"] == "success"
    assert data["fetched"] == 12
    assert data["created"] == 4


def test_crawler_run_rejects_unsupported_source(client):
    response = client.post("/api/v1/admin/crawler/run", json={"source": "unknown"})

    assert response.status_code == 200
    assert response.json()["code"] == 5001


def test_crawler_records_are_listed(client):
    response = client.get("/api/v1/admin/crawler/records")

    assert response.status_code == 200
    items = response.json()["data"]["items"]
    assert items[0]["source"] == "cs_zju"
    assert items[0]["status"] == "success"
    assert items[0]["fetched_count"] == 10
