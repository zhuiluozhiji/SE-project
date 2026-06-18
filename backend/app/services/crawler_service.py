"""爬虫业务逻辑层 —— 调度爬虫运行并管理爬取记录。

新增爬虫时只需在 SPIDER_REGISTRY 中注册一行，无需修改其他代码。
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.crawl_record import CrawlRecord

# ============================================================================
# 爬虫注册表 —— 新增爬虫只需在这里加一行
# ============================================================================
# 格式：{ source 标识: "模块路径:函数名" }
# source 标识对应 POST /api/v1/admin/crawler/run 中的 source 字段

SPIDER_REGISTRY: dict[str, str] = {
    "cs_zju": "crawler.spiders.cs_zju:crawl_and_save",
    "cse_zju": "crawler.spiders.cse_zju:crawl_and_save",
    "math_zju": "crawler.spiders.math_zju:crawl_and_save",
    "geo_zju": "crawler.spiders.geo_zju:crawl_and_save",
}

# ============================================================================
# 动态导入
# ============================================================================


def _ensure_project_root_on_path() -> None:
    """确保项目根目录在 sys.path 中（Docker 内 PYTHONPATH 可能不包含）。"""
    project_root = Path(__file__).resolve().parent.parent.parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))


def _get_spider_func(source: str):
    """根据 source 标识动态导入对应的爬虫入口函数。

    Args:
        source: 爬虫来源标识，如 "cs_zju"

    Returns:
        callable | None: crawl_and_save(db_session) 函数，未找到返回 None
    """
    if source not in SPIDER_REGISTRY:
        return None

    module_path, func_name = SPIDER_REGISTRY[source].split(":")

    _ensure_project_root_on_path()

    try:
        module = importlib.import_module(module_path)
        return getattr(module, func_name)
    except ImportError:
        # 可能是路径问题，再试一次
        try:
            module = importlib.import_module(module_path)
            return getattr(module, func_name)
        except (ImportError, AttributeError):
            return None


# ============================================================================
# 业务接口
# ============================================================================


def run_crawler_and_save(
    db: Session,
    source: str = "cs_zju",
    since: str | None = None,
    no_limit: bool = False,
) -> dict:
    """运行指定来源的爬虫并将结果写入数据库。

    Args:
        db: 数据库会话
        source: 爬虫来源标识，须在 SPIDER_REGISTRY 中注册
        since: 月份过滤 "YYYY-MM"，仅爬取此月及之后的活动；None 则使用爬虫默认 min_year
        no_limit: True 时不使用默认年份过滤，爬取该来源全部可用活动

    Returns:
        包含 status, fetched, created, skipped, error 等字段的字典
    """
    crawl_func = _get_spider_func(source)

    if crawl_func is None:
        return {
            "status": "error",
            "fetched": 0,
            "created": 0,
            "skipped": 0,
            "filtered": 0,
            "year_filtered": 0,
            "since_applied": since,
            "error": f"不支持的爬虫来源: {source}（未在 SPIDER_REGISTRY 中注册）",
        }

    try:
        effective_since = "__all__" if no_limit else since
        result = crawl_func(db, since=effective_since)
        return result
    except ImportError as exc:
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


def list_available_sources() -> list[str]:
    """返回所有已注册的爬虫 source 标识。"""
    return list(SPIDER_REGISTRY.keys())
