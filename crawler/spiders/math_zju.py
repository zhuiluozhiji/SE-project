"""Math ZJU 数学科学学院学术活动爬虫。

数学学院使用独立的 CMS 模板（非 WebPlus 通用模板），列表页已包含
主讲人、时间、地点等结构化信息，详情页有完整富文本正文。

架构：
- MathZJUSpider 继承 BaseSpider，实现列表页和详情页的 HTML 解析
- 通用逻辑（HTTP、字段抽取、过滤、入库）全部在 BaseSpider 中
"""

from __future__ import annotations

import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from crawler.spiders.base import BaseSpider, CrawledActivity


class MathZJUSpider(BaseSpider):
    """数学科学学院官网爬虫。

    覆盖 BaseSpider 的两个抽象方法：
        parse_activity_list()  — 数学学院列表页 HTML 解析
        parse_detail_page()    — 数学学院详情页 HTML 解析

    其余通用逻辑（HTTP、字段抽取、过滤、翻页、入库）由 BaseSpider 提供。
    """

    # ---- 爬虫标识 ----
    source = "math_zju"
    college = "数学科学学院"

    # ---- URL 配置 ----
    base_url = "http://www.math.zju.edu.cn"
    list_url = f"{base_url}/38073/list.htm"
    list_pattern = "/38073/list{page}.htm"
    max_pages = 60  # 实际约 58 页，多留余量，基类会自动提前停止

    # ---- 数学学院列表页常用前缀，用于分类判断 ----
    # 数学学院标题含"学术报告""学术讲座"等，不需要额外过滤关键词

    # ==================================================================
    # 列表页解析（数学学院特有 CSS 选择器）
    # ==================================================================

    def parse_activity_list(self, html: str) -> list[dict]:
        """从数学学院列表页 HTML 中提取活动条目。

        数学学院列表页结构：
            li.wow.fadeInUp > a[href]
                h3                               → 标题
                div.item > div.date
                    p.d                          → 日（如 "23"）
                    p.y                          → 年月（如 "2025-09"）
                div.item > div.info
                    p.peo                        → 主讲人
                    p.time                       → 时间
                    p.ad                         → 地点
        """
        soup = BeautifulSoup(html, "html.parser")
        items: list[dict] = []

        for li in soup.select("li.wow.fadeInUp"):
            link = li.select_one("a[href]")
            if link is None:
                continue

            href = link.get("href", "")
            if not href or "/page.htm" not in href:
                continue

            # 标题
            title_el = link.select_one("h3")
            title = title_el.get_text(strip=True) if title_el else ""
            if not title:
                continue

            # 日期：组合 p.d（日）+ p.y（年月）→ YYYY-MM-DD
            published_date = None
            date_div = link.select_one("div.date")
            if date_div:
                day_el = date_div.select_one("p.d")
                ym_el = date_div.select_one("p.y")
                day = day_el.get_text(strip=True) if day_el else ""
                ym = ym_el.get_text(strip=True) if ym_el else ""
                if ym and day:
                    # "2025-09" + "23" → "2025-09-23"
                    published_date = f"{ym}-{int(day):02d}"
                elif ym:
                    published_date = ym  # 回退到年月

            items.append({
                "title": title,
                "detail_url": urljoin(self.base_url, href),
                "published_date": published_date,
            })

        return items

    # ==================================================================
    # 详情页解析（数学学院特有 CSS 选择器 + 基类字段抽取）
    # ==================================================================

    def parse_detail_page(self, html: str, detail_url: str) -> CrawledActivity:
        """解析数学学院详情页。

        数学学院详情页结构：
            article > div.content
                h1.item_title                    → 标题
                div.item_info
                    span                         → 来源 / 发布时间 / 访问次数
                p.item_content
                    div.wp_articlecontent        → 正文（富文本 HTML）

        另外 <meta name="description"> 包含摘要文本，作为兜底。
        """
        soup = BeautifulSoup(html, "html.parser")

        # --- 标题 ---
        title = ""
        title_el = soup.select_one("h1.item_title")
        if title_el:
            title = title_el.get_text(strip=True)

        # --- 发布日期 & 来源 ---
        published_date = None
        author = None
        info_div = soup.select_one("div.item_info")
        if info_div:
            info_text = info_div.get_text(" ", strip=True)
            date_match = re.search(r"发布时间[：:]\s*(\d{4}-\d{2}-\d{2})", info_text)
            if date_match:
                published_date = date_match.group(1)
            source_match = re.search(r"来源[：:]\s*(\S+)", info_text)
            if source_match:
                author = source_match.group(1).strip()

        # --- 正文区域 ---
        description = ""
        content_el = soup.select_one("div.wp_articlecontent")
        if content_el:
            for tag in content_el.select("script, style, .wp_pdf_player"):
                tag.decompose()
            description = content_el.get_text("\n", strip=True)
            description = re.sub(r"\n{3,}", "\n\n", description)
        else:
            # 回退 1：尝试从 article 整体提取
            article_el = soup.find("article")
            if article_el:
                for tag in article_el.select(
                    "script, style, nav, footer, .top_title, .item_info"
                ):
                    tag.decompose()
                description = article_el.get_text("\n", strip=True)
                description = re.sub(r"\n{3,}", "\n\n", description)

        # 回退 2：如果正文为空或极短，尝试从 meta description 获取
        if len(description) < 30:
            meta_desc = soup.select_one("meta[name='description']")
            if meta_desc:
                meta_content = meta_desc.get("content", "")
                if meta_content and len(meta_content) > len(description):
                    description = meta_content

        if len(description) > 10000:
            description = description[:10000] + "\n\n[... 内容过长，已截断]"

        # --- 从正文中抽取结构化字段（基类提供，跨网站通用） ---
        fields = self._extract_structured_fields(title, description, published_date)

        # 如果正则没抽到主办方，默认用学院名
        organizer = fields["organizer"] or self.college

        # --- 判断是否跳过 ---
        skip, skip_reason = self._check_skip(title, description)

        return CrawledActivity(
            title=title,
            source_url=detail_url,
            published_date=published_date,
            description=description,
            author=author,
            speaker=fields["speaker"],
            start_time=fields["start_time"],
            end_time=fields["end_time"],
            location=fields["location"],
            campus=fields["campus"],
            category=fields["category"],
            organizer=organizer,
            college=self.college,
            skip=skip,
            skip_reason=skip_reason,
        )


# ============================================================================
# 模块级入口（供 crawler_service 通过注册表调用）
# ============================================================================

# 单例，避免每次调用都创建新实例
_spider_instance: MathZJUSpider | None = None


def _get_spider() -> MathZJUSpider:
    """获取 MathZJUSpider 单例。"""
    global _spider_instance
    if _spider_instance is None:
        _spider_instance = MathZJUSpider()
    return _spider_instance


def crawl_and_save(db_session, since: str | None = None) -> dict:
    """供后端 crawler_service 调用的入口函数。

    Args:
        db_session: SQLAlchemy 数据库会话
        since: "YYYY-MM" 月份过滤，如 "2026-03"；None 则使用爬虫默认 min_year
    """
    return _get_spider().crawl_and_save(db_session, since=since)


# ============================================================================
# 命令行入口
# ============================================================================

if __name__ == "__main__":
    MathZJUSpider().main()
