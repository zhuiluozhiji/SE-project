from pydantic import BaseModel


class CrawlerRunRequest(BaseModel):
    source: str = "cs_zju"
