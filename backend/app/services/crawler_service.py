"""爬虫业务逻辑层 —— 调度爬虫运行并管理爬取记录。"""

from __future__ import annotations

import sys
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.crawl_record import CrawlRecord


def _import_crawl_and_save():
    """导入爬虫核心函数，自动处理路径问题。"""
    try:
        from crawler.spiders.cs_zju import crawl_and_save
        return crawl_and_save
    except ImportError:
        # Docker 内 PYTHONPATH 可能不包含项目根目录，手动添加
        project_root = Path(__file__).resolve().parent.parent.parent.parent.parent
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))
        from crawler.spiders.cs_zju import crawl_and_save
        return crawl_and_save


def run_crawler_and_save(db: Session, source: str = "cs_zju") -> dict:
    """运行指定来源的爬虫并将结果写入数据库。

    Args:
        db: 数据库会话
        source: 爬虫来源标识，目前仅支持 "cs_zju"

    Returns:
        包含 status, fetched, created, skipped, error 的字典
    """
    if source != "cs_zju":
        return {
            "status": "error",
            "fetched": 0,
            "created": 0,
            "skipped": 0,
            "filtered": 0,
            "year_filtered": 0,
            "error": f"不支持的爬虫来源: {source}",
        }

    try:
        crawl_and_save = _import_crawl_and_save()
        result = crawl_and_save(db)
        return result
    except ImportError as exc:
        # 记录失败日志
        record = CrawlRecord(
            source=source,
            status="error",
            fetched_count=0,
            success_count=0,
            error_msg=f"ImportError: {exc}",
        )
        db.add(record)
        db.commit()
        return {
            "status": "error",
            "fetched": 0,
            "created": 0,
            "skipped": 0,
            "filtered": 0,
            "year_filtered": 0,
            "error": str(exc),
        }
    except Exception as exc:
        record = CrawlRecord(
            source=source,
            status="error",
            fetched_count=0,
            success_count=0,
            error_msg=str(exc),
        )
        db.add(record)
        db.commit()
        return {
            "status": "error",
            "fetched": 0,
            "created": 0,
            "skipped": 0,
            "filtered": 0,
            "year_filtered": 0,
            "error": str(exc),
        }


def get_crawler_records(db: Session, limit: int = 20) -> list[dict]:
    """获取最近的爬虫运行记录。"""
    records = db.scalars(
        select(CrawlRecord)
        .order_by(CrawlRecord.run_time.desc())
        .limit(limit)
    ).all()

    return [
        {
            "id": r.id,
            "source": r.source,
            "status": r.status,
            "fetched_count": r.fetched_count,
            "success_count": r.success_count,
            "error_msg": r.error_msg,
            "run_time": r.run_time.isoformat() if r.run_time else None,
        }
        for r in records
    ]
