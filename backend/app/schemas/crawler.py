from pydantic import BaseModel, field_validator


class CrawlerRunRequest(BaseModel):
    source: str = "cs_zju"
    since: str | None = None  # "YYYY-MM"，仅爬取此月及之后的活动；None 则使用爬虫默认 min_year

    @field_validator("since")
    @classmethod
    def validate_since(cls, v: str | None) -> str | None:
        """校验 since 格式为 YYYY-MM。"""
        if v is None:
            return v
        import re
        if not re.match(r"^\d{4}-\d{2}$", v):
            raise ValueError(f"since 格式必须为 YYYY-MM，例如 '2026-03'，收到: {v}")
        return v


class CrawlerRunResponse(BaseModel):
    status: str
    fetched: int = 0
    created: int = 0
    skipped: int = 0
    error: str | None = None
    since_applied: str | None = None  # 实际生效的月份过滤条件

