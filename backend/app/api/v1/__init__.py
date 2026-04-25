from fastapi import APIRouter

from app.api.v1 import activities, admin, auth, courses, crawler, recommendations, schedules, users

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(activities.router)
api_router.include_router(recommendations.router)
api_router.include_router(schedules.router)
api_router.include_router(courses.router)
api_router.include_router(admin.router)
api_router.include_router(crawler.router)
