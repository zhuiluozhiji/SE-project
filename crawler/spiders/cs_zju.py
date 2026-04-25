from dataclasses import dataclass

import requests
from bs4 import BeautifulSoup


@dataclass
class CrawledActivity:
    title: str
    source_url: str
    speaker: str | None = None
    start_time: str | None = None
    end_time: str | None = None
    location: str | None = None
    campus: str | None = None


def fetch_html(url: str) -> str:
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    response.encoding = response.apparent_encoding
    return response.text


def parse_activity_list(html: str, base_url: str) -> list[CrawledActivity]:
    soup = BeautifulSoup(html, "html.parser")
    items: list[CrawledActivity] = []
    for link in soup.select("a")[:20]:
      title = link.get_text(strip=True)
      href = link.get("href")
      if not title or not href:
          continue
      items.append(CrawledActivity(title=title, source_url=href if href.startswith("http") else base_url))
    return items


def main() -> None:
    print("Crawler skeleton is ready. Configure a real source URL before running.")


if __name__ == "__main__":
    main()
