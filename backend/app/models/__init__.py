from app.models.activity import Activity
from app.models.activity_interaction import ActivityInteraction
from app.models.activity_tag import ActivityTag
from app.models.course_schedule import CourseSchedule
from app.models.crawl_record import CrawlRecord
from app.models.schedule_event import ScheduleEvent
from app.models.user import User
from app.models.user_interest import UserInterest

__all__ = [
    "Activity",
    "ActivityInteraction",
    "ActivityTag",
    "CourseSchedule",
    "CrawlRecord",
    "ScheduleEvent",
    "User",
    "UserInterest",
]
