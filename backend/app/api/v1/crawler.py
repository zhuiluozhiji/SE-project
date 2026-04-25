from fastapi import APIRouter

from app.core.response import success
from app.schemas.crawler import CrawlerRunRequest

router = APIRouter(prefix="/admin/crawler", tags=["crawler"])


@router.post("/run")
def run_crawler(payload: CrawlerRunRequest):
    return success({"source": payload.source, "status": "queued"})


@router.get("/records")
def get_crawler_records():
    return success({"items": []})
