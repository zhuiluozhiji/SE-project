import csv
import io
from datetime import datetime, timedelta

from fastapi.testclient import TestClient
from openpyxl import Workbook
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.session import get_db
from app.main import app
from app.models.activity import Activity
from app.models.base import Base
from app.models.course_schedule import CourseSchedule
from app.models.schedule_event import ScheduleEvent
from app.models.user import User
from app.services.course_service import section_range_to_datetime


engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def setup_function():
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        db.add(
            User(
                id=1,
                username="student001",
                password_hash="dev-password-hash",
                role="student",
            )
        )
        start_time = datetime.now().replace(microsecond=0) + timedelta(days=1)
        end_time = start_time + timedelta(hours=2)
        db.add(
            Activity(
                id=101,
                title="人工智能前沿讲座",
                description="测试活动",
                speaker="张三教授",
                organizer="计算机学院",
                campus="紫金港",
                location="紫金港西区报告厅",
                start_time=start_time,
                end_time=end_time,
                status="open",
            )
        )
        db.add(
            ScheduleEvent(
                user_id=1,
                title="机器学习课程",
                type="course",
                start_time=start_time + timedelta(minutes=30),
                end_time=start_time + timedelta(hours=1, minutes=30),
                location="东1A-101",
                color_type="course",
            )
        )
        db.commit()
    finally:
        db.close()


def test_create_course_writes_course_and_schedule_event():
    response = client.post(
        "/api/v1/courses",
        json={
            "course_name": "软件工程",
            "weekday": 2,
            "start_section": 3,
            "end_section": 4,
            "location": "玉泉曹楼",
            "teacher": "李老师",
            "weeks": "1-16",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0
    assert data["data"]["course_name"] == "软件工程"

    db = TestingSessionLocal()
    try:
        assert db.query(CourseSchedule).count() == 1
        assert db.query(ScheduleEvent).filter_by(type="course").count() == 2
        assert db.query(ScheduleEvent).filter_by(title="软件工程").count() == 1
        assert db.query(ScheduleEvent).filter_by(title="软件工程课程").count() == 0
    finally:
        db.close()


def test_schedule_list_removes_legacy_course_title_suffix():
    response = client.get("/api/v1/schedules")

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0
    course_items = [item for item in data["data"]["items"] if item["type"] == "course"]
    assert course_items[0]["title"] == "机器学习"


def test_schedule_list_resolves_course_id_for_shifted_course_event():
    db = TestingSessionLocal()
    try:
        course = CourseSchedule(
            user_id=1,
            course_name="软件工程",
            teacher="李老师",
            weekday=2,
            start_section=3,
            end_section=4,
            weeks="1-16",
            location="玉泉曹楼",
        )
        db.add(course)
        db.flush()
        start_time, end_time = section_range_to_datetime(2, 3, 4)
        shifted_start = start_time + timedelta(days=7)
        shifted_end = end_time + timedelta(days=7)
        db.add(
            ScheduleEvent(
                user_id=1,
                title="软件工程课程",
                type="course",
                start_time=shifted_start,
                end_time=shifted_end,
                location="玉泉曹楼",
                color_type="blue",
            )
        )
        db.commit()
        course_id = course.id
    finally:
        db.close()

    response = client.get(
        "/api/v1/schedules",
        params={"start_date": shifted_start.date().isoformat(), "end_date": shifted_start.date().isoformat()},
    )

    assert response.status_code == 200
    data = response.json()
    item = next(item for item in data["data"]["items"] if item["title"] == "软件工程")
    assert item["course_id"] == course_id


def test_schedule_list_resolves_course_id_for_legacy_course_event_by_title_location():
    db = TestingSessionLocal()
    try:
        course = CourseSchedule(
            user_id=1,
            course_name="机器学习",
            teacher="李老师",
            weekday=1,
            start_section=3,
            end_section=4,
            weeks="1-16",
            location="东1A-101",
        )
        db.add(course)
        db.commit()
        course_id = course.id
    finally:
        db.close()

    response = client.get("/api/v1/schedules")

    assert response.status_code == 200
    data = response.json()
    item = next(item for item in data["data"]["items"] if item["title"] == "机器学习")
    assert item["course_id"] == course_id


def test_section_time_mapping_matches_school_schedule():
    start, end = section_range_to_datetime(1, 3, 5)
    assert start.strftime("%H:%M") == "10:00"
    assert end.strftime("%H:%M") == "12:25"

    start, end = section_range_to_datetime(2, 6, 7)
    assert start.strftime("%H:%M") == "13:25"
    assert end.strftime("%H:%M") == "15:00"

    start, end = section_range_to_datetime(3, 11, 13)
    assert start.strftime("%H:%M") == "18:50"
    assert end.strftime("%H:%M") == "21:15"


def test_schedule_list_expands_course_for_requested_academic_week():
    create_response = client.post(
        "/api/v1/courses",
        json={
            "course_name": "软件工程",
            "weekday": 2,
            "start_section": 3,
            "end_section": 4,
            "location": "玉泉曹楼",
            "teacher": "李老师",
            "weeks": "1-16",
        },
    )
    course_id = create_response.json()["data"]["id"]
    db = TestingSessionLocal()
    try:
        template_id = db.query(ScheduleEvent).filter_by(title="软件工程").one().id
    finally:
        db.close()

    response = client.get(
        "/api/v1/schedules",
        params={"start_date": "2026-05-25", "end_date": "2026-05-31"},
    )

    assert response.status_code == 200
    data = response.json()
    item = next(item for item in data["data"]["items"] if item["title"] == "软件工程")
    assert item["id"] == template_id
    assert item["course_id"] == course_id
    assert item["start_time"] == "2026-05-26T10:00:00"
    assert item["end_time"] == "2026-05-26T11:35:00"


def test_schedule_list_respects_course_week_range_and_parity():
    client.post(
        "/api/v1/courses",
        json={
            "course_name": "自然语言处理导论",
            "weekday": 2,
            "start_section": 3,
            "end_section": 4,
            "location": "玉泉教1-234",
            "teacher": "汤老师",
            "weeks": "1-16 双周",
        },
    )

    odd_response = client.get(
        "/api/v1/schedules",
        params={"start_date": "2026-05-25", "end_date": "2026-05-31"},
    )
    odd_titles = [item["title"] for item in odd_response.json()["data"]["items"]]
    assert "自然语言处理导论" not in odd_titles

    even_response = client.get(
        "/api/v1/schedules",
        params={"start_date": "2026-06-01", "end_date": "2026-06-07"},
    )
    even_items = even_response.json()["data"]["items"]
    item = next(item for item in even_items if item["title"] == "自然语言处理导论")
    assert item["start_time"] == "2026-06-02T10:00:00"

    out_of_range_response = client.get(
        "/api/v1/schedules",
        params={"start_date": "2026-06-22", "end_date": "2026-06-28"},
    )
    out_of_range_titles = [item["title"] for item in out_of_range_response.json()["data"]["items"]]
    assert "自然语言处理导论" not in out_of_range_titles


def test_delete_course_removes_matching_schedule_event():
    create_response = client.post(
        "/api/v1/courses",
        json={
            "course_name": "软件工程",
            "weekday": 2,
            "start_section": 3,
            "end_section": 4,
            "location": "玉泉曹楼",
            "teacher": "李老师",
            "weeks": "1-16",
        },
    )
    course_id = create_response.json()["data"]["id"]

    delete_response = client.delete(f"/api/v1/courses/{course_id}")
    assert delete_response.status_code == 200
    delete_data = delete_response.json()
    assert delete_data["code"] == 0
    assert delete_data["data"]["deleted_events"] == 1

    db = TestingSessionLocal()
    try:
        assert db.get(CourseSchedule, course_id) is None
        assert db.query(ScheduleEvent).filter_by(title="软件工程").count() == 0
    finally:
        db.close()


def test_delete_course_removes_legacy_course_event_by_title_location():
    db = TestingSessionLocal()
    try:
        course = CourseSchedule(
            user_id=1,
            course_name="机器学习",
            teacher="李老师",
            weekday=1,
            start_section=3,
            end_section=4,
            weeks="1-16",
            location="东1A-101",
        )
        db.add(course)
        db.commit()
        course_id = course.id
    finally:
        db.close()

    delete_response = client.delete(f"/api/v1/courses/{course_id}")

    assert delete_response.status_code == 200
    delete_data = delete_response.json()
    assert delete_data["code"] == 0
    assert delete_data["data"]["deleted_events"] == 1

    db = TestingSessionLocal()
    try:
        assert db.get(CourseSchedule, course_id) is None
        assert db.query(ScheduleEvent).filter_by(title="机器学习课程").count() == 0
    finally:
        db.close()


def test_delete_course_day_scope_removes_same_weekday_slots_only():
    course_ids = []
    for payload in [
        {
            "course_name": "软件工程",
            "weekday": 2,
            "start_section": 3,
            "end_section": 4,
            "location": "玉泉曹楼",
            "teacher": "李老师",
            "weeks": "1-16",
        },
        {
            "course_name": "软件工程",
            "weekday": 2,
            "start_section": 6,
            "end_section": 7,
            "location": "玉泉曹楼",
            "teacher": "李老师",
            "weeks": "1-16",
        },
        {
            "course_name": "软件工程",
            "weekday": 4,
            "start_section": 3,
            "end_section": 4,
            "location": "玉泉曹楼",
            "teacher": "李老师",
            "weeks": "1-16",
        },
    ]:
        response = client.post("/api/v1/courses", json=payload)
        assert response.status_code == 200
        course_ids.append(response.json()["data"]["id"])

    delete_response = client.delete(f"/api/v1/courses/{course_ids[0]}?scope=day")
    assert delete_response.status_code == 200
    delete_data = delete_response.json()
    assert delete_data["code"] == 0
    assert delete_data["data"]["scope"] == "day"
    assert delete_data["data"]["deleted_courses"] == 2
    assert delete_data["data"]["deleted_events"] == 2

    db = TestingSessionLocal()
    try:
        remaining = db.query(CourseSchedule).filter_by(course_name="软件工程").all()
        assert len(remaining) == 1
        assert remaining[0].id == course_ids[2]
        assert db.query(ScheduleEvent).filter_by(title="软件工程").count() == 1
    finally:
        db.close()


def test_delete_course_all_scope_removes_all_same_course_slots():
    course_ids = []
    for payload in [
        {
            "course_name": "数据库系统",
            "weekday": 1,
            "start_section": 1,
            "end_section": 2,
            "location": "紫金港东2",
            "teacher": "王老师",
            "weeks": "1-16",
        },
        {
            "course_name": "数据库系统",
            "weekday": 3,
            "start_section": 6,
            "end_section": 7,
            "location": "紫金港东2",
            "teacher": "王老师",
            "weeks": "1-16",
        },
        {
            "course_name": "软件工程",
            "weekday": 3,
            "start_section": 6,
            "end_section": 7,
            "location": "玉泉曹楼",
            "teacher": "李老师",
            "weeks": "1-16",
        },
    ]:
        response = client.post("/api/v1/courses", json=payload)
        assert response.status_code == 200
        course_ids.append(response.json()["data"]["id"])

    delete_response = client.delete(f"/api/v1/courses/{course_ids[0]}?scope=all")
    assert delete_response.status_code == 200
    delete_data = delete_response.json()
    assert delete_data["code"] == 0
    assert delete_data["data"]["scope"] == "all"
    assert delete_data["data"]["deleted_courses"] == 2
    assert delete_data["data"]["deleted_events"] == 2

    db = TestingSessionLocal()
    try:
        assert db.query(CourseSchedule).filter_by(course_name="数据库系统").count() == 0
        assert db.query(ScheduleEvent).filter_by(title="数据库系统").count() == 0
        assert db.query(CourseSchedule).filter_by(course_name="软件工程").count() == 1
    finally:
        db.close()


def test_activity_list_and_detail_use_database_ids():
    list_response = client.get("/api/v1/activities")
    assert list_response.status_code == 200
    list_data = list_response.json()
    assert list_data["code"] == 0
    assert list_data["data"]["items"][0]["id"] == 101

    detail_response = client.get("/api/v1/activities/101")
    assert detail_response.status_code == 200
    detail_data = detail_response.json()
    assert detail_data["code"] == 0
    assert detail_data["data"]["title"] == "人工智能前沿讲座"


def test_check_conflict_returns_course_conflict():
    response = client.post("/api/v1/schedules/check-conflict", json={"activity_id": 101})

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0
    assert data["data"]["has_conflict"] is True
    assert data["data"]["conflicts"][0]["title"] == "机器学习"


def test_add_activity_requires_force_when_conflicted():
    response = client.post(
        "/api/v1/schedules/add-activity",
        json={"activity_id": 101, "force_add": False},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 3003
    assert "冲突" in data["message"]


def test_force_add_activity_and_export_ics():
    add_response = client.post(
        "/api/v1/schedules/add-activity",
        json={"activity_id": 101, "force_add": True},
    )
    assert add_response.status_code == 200
    add_data = add_response.json()
    assert add_data["code"] == 0
    assert add_data["data"]["has_conflict"] is True

    list_response = client.get("/api/v1/schedules")
    assert list_response.status_code == 200
    titles = [item["title"] for item in list_response.json()["data"]["items"]]
    assert "人工智能前沿讲座" in titles

    export_meta_response = client.get("/api/v1/schedules/export-ics")
    assert export_meta_response.status_code == 200
    assert export_meta_response.json()["code"] == 0
    assert export_meta_response.json()["data"]["download_url"].endswith("/export-ics/file")

    export_response = client.get("/api/v1/schedules/export-ics/file")
    assert export_response.status_code == 200
    assert "text/calendar" in export_response.headers["content-type"]
    assert "BEGIN:VCALENDAR" in export_response.text
    assert "人工智能前沿讲座" in export_response.text


def test_add_custom_activity_schedule_from_recognized_text_requires_force_when_conflicted():
    db = TestingSessionLocal()
    try:
        activity = db.get(Activity, 101)
        payload = {
            "title": "截图识别活动",
            "location": "紫金港东1A-101",
            "start_time": activity.start_time.isoformat(),
            "end_time": activity.end_time.isoformat(),
            "remark": "截图补充备注",
            "marker_label": "讲",
            "color_type": "green",
        }
    finally:
        db.close()

    check_response = client.post("/api/v1/schedules/check-custom-event", json=payload)
    assert check_response.status_code == 200
    check_data = check_response.json()
    assert check_data["code"] == 0
    assert check_data["data"]["has_conflict"] is True
    assert check_data["data"]["conflicts"][0]["title"] == "机器学习"

    reject_response = client.post(
        "/api/v1/schedules/add-custom-event",
        json={**payload, "force_add": False},
    )
    assert reject_response.status_code == 200
    reject_data = reject_response.json()
    assert reject_data["code"] == 3007
    assert "冲突" in reject_data["message"]

    add_response = client.post(
        "/api/v1/schedules/add-custom-event",
        json={**payload, "force_add": True},
    )
    assert add_response.status_code == 200
    add_data = add_response.json()
    assert add_data["code"] == 0
    assert add_data["data"]["activity_id"] is None
    assert add_data["data"]["has_conflict"] is True

    list_response = client.get("/api/v1/schedules")
    items = list_response.json()["data"]["items"]
    added = next(item for item in items if item["title"] == "截图识别活动")
    assert added["type"] == "activity"
    assert added["marker_label"] == "讲"
    assert added["remark"] == "截图补充备注"


def test_update_activity_schedule_color():
    add_response = client.post(
        "/api/v1/schedules/add-activity",
        json={"activity_id": 101, "force_add": True},
    )
    schedule_id = add_response.json()["data"]["schedule_id"]

    response = client.patch(
        f"/api/v1/schedules/{schedule_id}/appearance",
        json={"color_type": "pink", "marker_label": "讲", "remark": "活动备注"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0
    assert data["data"]["color_type"] == "pink"
    assert data["data"]["marker_label"] == "讲"
    assert data["data"]["remark"] == "活动备注"

    list_response = client.get("/api/v1/schedules")
    items = list_response.json()["data"]["items"]
    updated = next(item for item in items if item["id"] == schedule_id)
    assert updated["color_type"] == "pink"
    assert updated["marker_label"] == "讲"
    assert updated["remark"] == "活动备注"


def test_update_course_schedule_appearance():
    list_response = client.get("/api/v1/schedules")
    course_event = next(item for item in list_response.json()["data"]["items"] if item["type"] == "course")

    response = client.patch(
        f"/api/v1/schedules/{course_event['id']}/appearance",
        json={"color_type": "purple", "marker_label": "实", "remark": "课程备注"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0
    assert data["data"]["type"] == "course"
    assert data["data"]["color_type"] == "purple"
    assert data["data"]["marker_label"] == "实"
    assert data["data"]["remark"] == "课程备注"

    list_response = client.get("/api/v1/schedules")
    course_items = [item for item in list_response.json()["data"]["items"] if item["type"] == "course"]
    assert any(item["remark"] == "课程备注" for item in course_items)


def test_delete_activity_schedule_event_only():
    add_response = client.post(
        "/api/v1/schedules/add-activity",
        json={"activity_id": 101, "force_add": True},
    )
    schedule_id = add_response.json()["data"]["schedule_id"]

    response = client.delete(f"/api/v1/schedules/{schedule_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0
    assert data["data"]["activity_id"] == 101

    db = TestingSessionLocal()
    try:
        assert db.get(ScheduleEvent, schedule_id) is None
        assert db.get(Activity, 101) is not None
    finally:
        db.close()


def test_import_courses_from_csv():
    buffer = io.StringIO()
    writer = csv.DictWriter(
        buffer,
        fieldnames=["课程名", "星期", "节次", "地点", "教师", "周次"],
    )
    writer.writeheader()
    writer.writerow(
        {
            "课程名": "数据库系统",
            "星期": "周三",
            "节次": "6-7",
            "地点": "紫金港东2",
            "教师": "王老师",
            "周次": "1-16",
        }
    )

    response = client.post(
        "/api/v1/courses/import",
        files={"file": ("courses.csv", buffer.getvalue().encode("utf-8"), "text/csv")},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0
    assert data["data"]["imported_count"] == 1
    assert data["data"]["courses"][0]["course_name"] == "数据库系统"
    assert data["data"]["example"]["headers"][0] == "课程名"


def test_import_courses_reports_missing_headers_with_example():
    response = client.post(
        "/api/v1/courses/import",
        files={"file": ("bad.csv", "名称,地点\n数据库系统,紫金港东2\n".encode("utf-8"), "text/csv")},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 2002
    assert "支持普通模板表头" in data["message"]
    assert "教务导出表头" in data["message"]


def test_import_courses_reports_empty_file():
    response = client.post(
        "/api/v1/courses/import",
        files={"file": ("empty.csv", "课程名,星期,节次\n".encode("utf-8"), "text/csv")},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 2002
    assert "至少一行课程数据" in data["message"]


def test_import_zju_export_xlsx_style_csv_rows():
    content = "\n".join(
        [
            "2025-2026学年春夏学期李妍雅的课表",
            "课程代码,课程名称,教师姓名,学期,上课时间,上课地点,选课时间,选课志愿",
            "CS3100M,编译原理,刘忠鑫,春夏,\"周一第3,4,5节;周三第1,2节\",玉泉教4-310;玉泉曹光彪西-503,2025-12-19 11:59:10,1.0",
            "CS3221M,自然语言处理导论,汤斯亮,春夏,\"周二第3,4节{单周};周二第3,4,5节{双周}\",玉泉教1-234;玉泉教1-234,2026-03-04 22:26:30,1.0",
        ]
    )

    response = client.post(
        "/api/v1/courses/import",
        files={"file": ("zju.csv", content.encode("utf-8"), "text/csv")},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0
    assert data["data"]["imported_count"] == 4
    courses = data["data"]["courses"]
    assert courses[0]["course_name"] == "编译原理"
    assert courses[0]["weekday"] == 1
    assert courses[0]["start_section"] == 3
    assert courses[0]["end_section"] == 5
    assert courses[1]["weekday"] == 3
    assert courses[1]["location"] == "玉泉曹光彪西-503"
    assert courses[2]["weeks"] == "春夏 单周"


def test_import_zju_export_xlsx_file():
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(["2025-2026学年春夏学期李妍雅的课表"])
    sheet.append(["课程代码", "课程名称", "教师姓名", "学期", "上课时间", "上课地点", "选课时间", "选课志愿"])
    sheet.append(
        [
            "CS3100M",
            "编译原理",
            "刘忠鑫",
            "春夏",
            "周一第3,4,5节;周三第1,2节",
            "玉泉教4-310;玉泉曹光彪西-503",
            "2025-12-19 11:59:10",
            "1.0",
        ]
    )
    sheet.append(
        [
            "CS3221M",
            "自然语言处理导论",
            "汤斯亮",
            "春夏",
            "周二第3,4节{单周};周二第3,4,5节{双周};周四第1,2节",
            "玉泉教1-234;玉泉教1-234;玉泉曹光彪西-503",
            "2026-03-04 22:26:30",
            "1.0",
        ]
    )
    buffer = io.BytesIO()
    workbook.save(buffer)

    response = client.post(
        "/api/v1/courses/import",
        files={
            "file": (
                "课表_3230106240.xlsx",
                buffer.getvalue(),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0
    assert data["data"]["imported_count"] == 5
    courses = data["data"]["courses"]
    assert courses[0]["course_name"] == "编译原理"
    assert courses[0]["weekday"] == 1
    assert courses[0]["start_section"] == 3
    assert courses[0]["end_section"] == 5
    assert courses[1]["weekday"] == 3
    assert courses[1]["location"] == "玉泉曹光彪西-503"
    assert courses[2]["weeks"] == "春夏 单周"
    assert courses[3]["weeks"] == "春夏 双周"
    assert courses[4]["weekday"] == 4
