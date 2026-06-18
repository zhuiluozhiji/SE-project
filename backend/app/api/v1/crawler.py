from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.response import fail, success
from app.db.session import get_db
from app.schemas.crawler import CrawlerRunRequest
from app.services.crawler_service import (
    get_crawler_records,
    list_available_sources,
    run_crawler_and_save,
)

router = APIRouter(prefix="/admin/crawler", tags=["crawler"])


@router.get("/sources")
def get_crawler_sources():
    """获取所有可用的爬虫来源列表。"""
    sources = list_available_sources()
    return success({"sources": sources})


@router.post("/run")
def run_crawler(payload: CrawlerRunRequest, db: Session = Depends(get_db)):
    """触发爬虫任务：抓取学院官网学生活动列表并存入数据库。

    支持 since 月份过滤（YYYY-MM），仅爬取该月及之后的活动。
    不传 since 则使用爬虫默认的 min_year 配置；no_limit=true 时不使用默认年份过滤。
    """
    result = run_crawler_and_save(
        db,
        source=payload.source,
        since=payload.since,
        no_limit=payload.no_limit,
    )
    if result.get("status") in ("error", "empty"):
        return fail(code=5001, message=result.get("error", "爬虫运行失败，未获取到任何活动"))
    return success({
        "source": payload.source,
        "status": result.get("status", "unknown"),
        "fetched": result.get("fetched", 0),
        "created": result.get("created", 0),
        "skipped": result.get("skipped", 0),
        "filtered": result.get("filtered", 0),
        "year_filtered": result.get("year_filtered", 0),
        "since_applied": result.get("since_applied"),
    })


@router.get("/records")
def list_crawler_records(db: Session = Depends(get_db)):
    """查看爬虫运行历史记录。"""
    records = get_crawler_records(db)
    return success({"items": records})
