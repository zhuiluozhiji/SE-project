"""数据存储管道 —— 爬取结果写入数据库。

注意：爬虫的入库逻辑统一在 BaseSpider.save_activities_to_db() 中实现。
所有学院爬虫通过 BaseSpider.crawl_and_save(db_session) 完成「抓取 → 过滤 → 入库」。
本模块保留作为自定义管道的扩展入口。
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session


def save_activities(
    activities: list[dict],
    db: Session,
    *,
    source: str = "unknown",
) -> int:
    """将爬取的活动数据写入数据库（独立于 BaseSpider 的轻量入口）。

    去重策略：按 source_url 判断是否已存在。

    Args:
        activities: 活动数据字典列表，每个字典应包含：
            title, source_url, published_date, description,
            speaker, organizer, college, category, campus, location,
            start_time, end_time
        db: SQLAlchemy 数据库会话
        source: 爬虫来源标识（如 "cs_zju"），用于 CrawlRecord

    Returns:
        成功写入的条数
    """
    from app.models.activity import Activity
    from app.models.crawl_record import CrawlRecord

    created = 0
    skipped_dup = 0

    for a in activities:
        source_url = a.get("source_url", "")
        if not source_url:
            continue

        existing = db.scalar(
            select(Activity).where(Activity.source_url == source_url)
        )
        if existing is not None:
            skipped_dup += 1
            continue

        # 解析日期时间
        start_time = _parse_datetime(a.get("start_time"))
        end_time = _parse_datetime(a.get("end_time"))

        activity = Activity(
            title=a.get("title") or "未命名活动",
            description=a.get("description"),
            speaker=a.get("speaker"),
            organizer=a.get("organizer"),
            college=a.get("college"),
            category=a.get("category"),
            campus=a.get("campus"),
            location=a.get("location"),
            start_time=start_time,
            end_time=end_time,
            source_url=source_url,
            source_type="crawled",
            hot_score=0,
            status="open",
        )
        db.add(activity)
        created += 1

    db.commit()

    record = CrawlRecord(
        source=source,
        status="success",
        fetched_count=len(activities),
        success_count=created,
        error_msg=f"dup_skipped={skipped_dup}" if skipped_dup else None,
    )
    db.add(record)
    db.commit()

    return created


def _parse_datetime(value: str | None) -> datetime | None:
    """将多种日期时间字符串统一转换为 datetime 对象。"""
    if not value:
        return None
    formats = [
        "%Y-%m-%d %H:%M",
        "%Y-%m-%dT%H:%M",
        "%Y-%m-%d",
        "%Y年%m月%d日 %H:%M",
        "%Y年%m月%d日",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None
