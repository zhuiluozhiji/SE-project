"""CS ZJU 学院官网学生活动爬虫。

功能：
- 翻页抓取全部列表页（/27181/list.htm 至 list15.htm）
- 逐条进入详情页提取正文内容
- 从正文中智能抽取结构化字段（时间、地点、主讲人、主办方、校区、类别）
- 过滤总结/公示/回顾类帖子，仅保留活动、赛事、讲座通知
- 支持将结果写入数据库

架构：
- CSZJUSpider 继承 BaseSpider，仅实现网站特有的 HTML 解析逻辑
- 通用逻辑（HTTP、字段抽取、过滤、入库）全部在 BaseSpider 中
- 如需爬取 CS 学院其他栏目，继承 CSZJUSpider 并覆盖 URL 配置即可
"""

from __future__ import annotations

import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from crawler.spiders.base import BaseSpider, CrawledActivity


class CSZJUSpider(BaseSpider):
    """CS ZJU 学院官网爬虫。

    覆盖 BaseSpider 的两个抽象方法：
        parse_activity_list()  — CS 学院列表页 HTML 解析
        parse_detail_page()    — CS 学院详情页 HTML 解析

    其余通用逻辑（HTTP、字段抽取、过滤、翻页、入库）由 BaseSpider 提供。
    """

    # ---- 爬虫标识 ----
    source = "cs_zju"
    college = "计算机科学与技术学院"

    # ---- URL 配置 ----
    base_url = "http://cspo.zju.edu.cn"
    list_url = f"{base_url}/27181/list.htm"
    list_pattern = "/27181/list{page}.htm"
    max_pages = 15

    # ==================================================================
    # 列表页解析（CS 学院特有 CSS 选择器）
    # ==================================================================

    def parse_activity_list(self, html: str) -> list[dict]:
        """从 CS ZJU 列表页 HTML 中提取活动条目。

        CS 学院列表页结构：
            div.jzlb.clearfix > div.btt3 > a （标题+链接）
            div.jzlb.clearfix > div.fbsj4        （发布日期）
        """
        soup = BeautifulSoup(html, "html.parser")
        items: list[dict] = []

        for row in soup.select("div.jzlb.clearfix"):
            title_el = row.select_one("div.btt3 a")
            if title_el is None:
                continue
            title = title_el.get_text(strip=True)
            href = title_el.get("href", "")
            if not title or not href:
                continue

            date_el = row.select_one("div.fbsj4")
            date_text = date_el.get_text(strip=True) if date_el else None

            items.append({
                "title": title,
                "detail_url": urljoin(self.base_url, href),
                "published_date": date_text,
            })

        return items

    # ==================================================================
    # 详情页解析（CS 学院特有 CSS 选择器 + 基类字段抽取）
    # ==================================================================

    def parse_detail_page(self, html: str, detail_url: str) -> CrawledActivity:
        """解析 CS ZJU 详情页。

        CS 学院详情页结构：
            h1.wp_articleTitle / h1.arti_title     → 标题
            div.wp_articlecontent / div.arti_content → 正文
            div.wp_articleAuthor / div.arti_metas   → 作者
            div.wp_articleDate / span.wp_articleDate → 发布日期
        """
        soup = BeautifulSoup(html, "html.parser")

        # --- 标题 ---
        title = ""
        title_el = soup.select_one(
            "h1.wp_articleTitle, h1.arti_title, h1, .arti_title"
        )
        if title_el:
            title = title_el.get_text(strip=True)

        # --- 正文区域 ---
        description = ""
        content_el = soup.select_one(
            "div.wp_articlecontent, div.arti_content, "
            "div.entry-content, div.wp_column, div.col_news_con, "
            "div#content, article"
        )
        if content_el:
            for tag in content_el.select("script, style"):
                tag.decompose()
            description = content_el.get_text("\n", strip=True)
            description = re.sub(r"\n{3,}", "\n\n", description)
        else:
            body = soup.find("body")
            if body:
                for tag in body.select(
                    "script, style, nav, footer, .top-nav, .foot-1, .wp-navi-aside"
                ):
                    tag.decompose()
                description = body.get_text("\n", strip=True)
                description = re.sub(r"\n{3,}", "\n\n", description)

        if len(description) > 10000:
            description = description[:10000] + "\n\n[... 内容过长，已截断]"

        # --- 作者 ---
        author = None
        meta_line = soup.select_one(
            "div.wp_articleAuthor, div.arti_metas, p.author, span.author, "
            "div.col_news_metas, .fl"
        )
        if meta_line:
            meta_text = meta_line.get_text(strip=True)
            author_match = re.search(r"发布者[：:]\s*(\S+)", meta_text)
            if author_match:
                author = author_match.group(1)

        # --- 发布日期 ---
        published_date = None
        date_meta = soup.select_one(
            "div.wp_articleDate, span.wp_articleDate, span.date, time, "
            "div.col_news_metas, .fl"
        )
        if date_meta:
            date_text = date_meta.get_text(strip=True)
            date_match = re.search(r"(\d{4}-\d{2}-\d{2})", date_text)
            if date_match:
                published_date = date_match.group(1)

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
_spider_instance: CSZJUSpider | None = None


def _get_spider() -> CSZJUSpider:
    """获取 CSZJUSpider 单例。"""
    global _spider_instance
    if _spider_instance is None:
        _spider_instance = CSZJUSpider()
    return _spider_instance


def crawl_and_save(db_session) -> dict:
    """供后端 crawler_service 调用的入口函数。

    保持向后兼容：crawler_service 仍然 import 此函数名。
    """
    return _get_spider().crawl_and_save(db_session)


# ============================================================================
# 命令行入口
# ============================================================================

if __name__ == "__main__":
    CSZJUSpider().main()

