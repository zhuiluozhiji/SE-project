from pydantic import BaseModel


class CrawlerRunRequest(BaseModel):
    source: str = "cs_zju"


class CrawlerRunResponse(BaseModel):
    status: str
    fetched: int = 0
    created: int = 0
    skipped: int = 0
    error: str | None = None

