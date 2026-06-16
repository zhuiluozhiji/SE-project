"""Geo ZJU 地球科学学院学术活动爬虫。

地球科学学院使用独立 CMS 模板，结构与数学学院类似但 CSS 类名不同。
列表页包含日期、主讲人、时间、地点等结构化字段（但部分字段可能为空），
详情页有完整富文本正文。

架构：
- GeoZJUSpider 继承 BaseSpider，实现列表页和详情页的 HTML 解析
- 通用逻辑（HTTP、字段抽取、过滤、入库）全部在 BaseSpider 中
"""

from __future__ import annotations

import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from crawler.spiders.base import BaseSpider, CrawledActivity


class GeoZJUSpider(BaseSpider):
    """地球科学学院官网爬虫。

    覆盖 BaseSpider 的两个抽象方法：
        parse_activity_list()  — 地科学院列表页 HTML 解析
        parse_detail_page()    — 地科学院详情页 HTML 解析

    其余通用逻辑（HTTP、字段抽取、过滤、翻页、入库）由 BaseSpider 提供。
    """

    # ---- 爬虫标识 ----
    source = "geo_zju"
    college = "地球科学学院"

    # ---- URL 配置 ----
    base_url = "http://gs.zju.edu.cn"
    list_url = f"{base_url}/34771/list.htm"
    list_pattern = "/34771/list{page}.htm"
    max_pages = 25  # 实际约 23 页，多留余量，基类会自动提前停止

    # ==================================================================
    # 列表页解析（地科学院特有 CSS 选择器）
    # ==================================================================

    def parse_activity_list(self, html: str) -> list[dict]:
        """从地科学院列表页 HTML 中提取活动条目。

        地科学院列表页结构：
            li.list-acad
                a[href]                              → 标题（title 属性）
                div.acad-time
                    span                             → 日（如 "09"）
                    文本节点                          → 年月（如 "2026-06"）
                div.acad-con
                    p.acad-con-speaker                → 主讲人（内容可能不准确）
                    p.acad-con-time                  → 时间
                    p.acad-con-place                 → 地点

        注：列表页的结构化字段（主讲人/时间/地点）部分条目为空或内容错位，
        最终数据以详情页正文为准。
        """
        soup = BeautifulSoup(html, "html.parser")
        items: list[dict] = []

        for li in soup.select("li.list-acad"):
            link = li.select_one("a[href]")
            if link is None:
                continue

            href = link.get("href", "")
            if not href or "/page.htm" not in href:
                continue

            # 标题：优先使用 title 属性（更完整），回退到链接文本
            title = link.get("title", "") or link.get_text(strip=True)
            if not title:
                continue

            # 日期：组合 span（日）+ 后续文本（年月）→ YYYY-MM-DD
            published_date = None
            time_div = li.select_one("div.acad-time")
            if time_div:
                day_el = time_div.select_one("span")
                day = day_el.get_text(strip=True) if day_el else ""
                # 获取 span 之后的文本节点
                ym_text = ""
                if day_el:
                    for sibling in day_el.next_siblings:
                        text = sibling.get_text(strip=True) if hasattr(sibling, "get_text") else str(sibling).strip()
                        if text:
                            ym_text = text
                            break
                # 提取 YYYY-MM 格式
                ym_match = re.search(r"(\d{4}-\d{2})", ym_text) if ym_text else None
                ym = ym_match.group(1) if ym_match else ""
                if ym and day and day.isdigit():
                    published_date = f"{ym}-{int(day):02d}"
                elif ym:
                    published_date = ym

            items.append({
                "title": title,
                "detail_url": urljoin(self.base_url, href),
                "published_date": published_date,
            })

        return items

    # ==================================================================
    # 详情页解析（地科学院特有 CSS 选择器 + 基类字段抽取）
    # ==================================================================

    def parse_detail_page(self, html: str, detail_url: str) -> CrawledActivity:
        """解析地科学院详情页。

        地科学院详情页结构：
            div.content_r
                div.content_title
                    h2                                → 标题
                    div.cont_tit
                        span                          → 编辑 / 时间 / 访问次数
                div.content_main
                    div.wp_articlecontent             → 正文（富文本 HTML）

        另外 <meta name="description"> 包含摘要文本，作为兜底。
        """
        soup = BeautifulSoup(html, "html.parser")

        # --- 标题 ---
        title = ""
        title_el = soup.select_one("div.content_title h2")
        if title_el:
            title = title_el.get_text(strip=True)

        # --- 发布日期 ---
        published_date = None
        cont_tit = soup.select_one("div.cont_tit")
        if cont_tit:
            tit_text = cont_tit.get_text(" ", strip=True)
            date_match = re.search(r"时间[：:]\s*(\d{4}-\d{2}-\d{2})", tit_text)
            if date_match:
                published_date = date_match.group(1)

        # --- 正文区域 ---
        description = ""
        content_el = soup.select_one("div.wp_articlecontent")
        if content_el:
            for tag in content_el.select("script, style"):
                tag.decompose()
            description = content_el.get_text("\n", strip=True)
            description = re.sub(r"\n{3,}", "\n\n", description)

        # 回退：如果正文为空或极短，尝试从 meta description 获取
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
            author=None,
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
_spider_instance: GeoZJUSpider | None = None


def _get_spider() -> GeoZJUSpider:
    """获取 GeoZJUSpider 单例。"""
    global _spider_instance
    if _spider_instance is None:
        _spider_instance = GeoZJUSpider()
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
    GeoZJUSpider().main()
