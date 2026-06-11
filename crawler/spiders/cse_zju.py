"""CSE ZJU 控制科学与工程学院科研学术活动爬虫。

控制学院与计院使用同一套 CMS 模板（WebPlus），但详情页内容有所不同：
- 部分活动详情页仅有海报图片，无文字正文
- 对于海报图片，自动调用 OCR 服务提取结构化信息
- OCR 不可用或失败时，保留图片 URL 供人工处理

架构：
- CSEZJUSpider 继承 BaseSpider，实现列表页和详情页的 HTML 解析
- 通用逻辑（HTTP、字段抽取、过滤、入库）全部在 BaseSpider 中
"""

from __future__ import annotations

import re
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from crawler.spiders.base import BaseSpider, CrawledActivity


class CSEZJUSpider(BaseSpider):
    """控制科学与工程学院官网爬虫。

    覆盖 BaseSpider 的两个抽象方法：
        parse_activity_list()  — 控制学院列表页 HTML 解析
        parse_detail_page()    — 控制学院详情页 HTML 解析（含海报 OCR）

    其余通用逻辑（HTTP、字段抽取、过滤、翻页、入库）由 BaseSpider 提供。
    """

    # ---- 爬虫标识 ----
    source = "cse_zju"
    college = "控制科学与工程学院"

    # ---- URL 配置 ----
    base_url = "http://www.cse.zju.edu.cn"
    list_url = f"{base_url}/39312/list.htm"
    list_pattern = "/39312/list{page}.htm"
    max_pages = 20

    # ---- 过滤配置 ----
    # 控制学院列表中有「公示」类帖子，使用基类默认关键词即可过滤

    # ==================================================================
    # 列表页解析（控制学院特有 CSS 选择器）
    # ==================================================================

    def parse_activity_list(self, html: str) -> list[dict]:
        """从控制学院列表页 HTML 中提取活动条目。

        控制学院列表页结构（与计院同为 WebPlus CMS，但 CSS 类名不同）：
            li > div.con1rm2r.f > div.con1rm2rt.xi20 > a （标题+链接）
            li > div.con1rm2l.xi20                        （发布日期）
        """
        soup = BeautifulSoup(html, "html.parser")
        items: list[dict] = []

        for row in soup.select("div.con1rm2r.f"):
            title_el = row.select_one("div.con1rm2rt.xi20 a")
            if title_el is None:
                continue
            # 优先使用 title 属性（完整），回退到 span.con-title 文本
            title = title_el.get("title", "") or title_el.get_text(strip=True)
            href = title_el.get("href", "")
            if not title or not href:
                continue

            # 日期在兄弟 div.con1rm2l.xi20 中
            parent_li = row.find_parent("li")
            date_el = None
            if parent_li:
                date_el = parent_li.select_one("div.con1rm2l.xi20")
            date_text = date_el.get_text(strip=True) if date_el else None

            items.append({
                "title": title,
                "detail_url": urljoin(self.base_url, href),
                "published_date": date_text,
            })

        return items

    # ==================================================================
    # 详情页解析（控制学院特有 CSS 选择器 + 海报 OCR）
    # ==================================================================

    def parse_detail_page(self, html: str, detail_url: str) -> CrawledActivity:
        """解析控制学院详情页。

        控制学院详情页结构：
            div.cg-customize-content.article-content
                div.con2t.mg2.xi24.cen          → 标题 + 元信息
                    span.xi14                    → 时间、来源、编辑、访问次数
                div.con2f.mg2
                    div.wp_articlecontent        → 正文（可能是纯海报图片）

        对于仅含海报图片的页面，自动下载图片并调用 OCR 识别。
        """
        soup = BeautifulSoup(html, "html.parser")

        # --- 标题 ---
        title = ""
        title_div = soup.select_one("div.con2t.mg2.xi24.cen")
        if title_div:
            # 标题是 div 的第一个文本节点（<br> 之前的内容）
            title_text = title_div.get_text("\n", strip=True)
            # 取第一行作为标题（排除元信息行）
            for line in title_text.split("\n"):
                line = line.strip()
                if line and not line.startswith("时间：") and not line.startswith("来源：") \
                        and not line.startswith("编辑：") and not line.startswith("访问次数"):
                    title = line
                    break

        # --- 元信息（时间、来源） ---
        published_date = None
        author = None
        meta_span = soup.select_one("div.con2t.mg2.xi24.cen span.xi14")
        if meta_span:
            meta_text = meta_span.get_text(" ", strip=True)
            # 提取日期
            date_match = re.search(r"时间[：:]\s*(\d{4}-\d{2}-\d{2})", meta_text)
            if date_match:
                published_date = date_match.group(1)
            # 提取来源/发布者
            source_match = re.search(r"来源[：:]\s*(\S+)", meta_text)
            if source_match:
                author = source_match.group(1).strip()

        # --- 正文区域 ---
        description = ""
        poster_image_url: str | None = None
        content_el = soup.select_one("div.wp_articlecontent")

        if content_el:
            # 移除脚本和样式
            for tag in content_el.select("script, style"):
                tag.decompose()

            # 提取正文文本
            text_content = content_el.get_text("\n", strip=True)
            text_content = re.sub(r"\n{3,}", "\n\n", text_content)

            # 查找所有 img 标签
            img_tags = content_el.select("img")
            for img in img_tags:
                src = img.get("src", "")
                if src:
                    # 过滤掉统计像素（visitcount 等）
                    if any(skip in src.lower() for skip in ["visitcount", "visitcountdisplay"]):
                        continue
                    poster_image_url = urljoin(self.base_url, src)
                    break  # 通常只有一张海报

            if text_content:
                description = text_content
            elif poster_image_url:
                # 正文无文字，仅有海报图片 → 尝试 OCR
                ocr_text = self._try_ocr_poster(poster_image_url)
                if ocr_text:
                    description = (
                        f"[OCR 识别结果]\n{ocr_text}\n\n"
                        f"[原始海报: {poster_image_url}]"
                    )
                else:
                    description = (
                        f"[此活动详情页仅含海报图片，暂未识别。"
                        f"请通过后台「识别截图」功能手动处理。]\n"
                        f"海报地址: {poster_image_url}"
                    )
        else:
            # 无正文区域，尝试从 body 提取
            body = soup.find("body")
            if body:
                for tag in body.select(
                    "script, style, nav, footer, .top-nav, .foot-1, .header-top, "
                    ".m-footer, .wp-navi-aside, .con1rtr"
                ):
                    tag.decompose()
                description = body.get_text("\n", strip=True)
                description = re.sub(r"\n{3,}", "\n\n", description)

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

    # ==================================================================
    # 海报 OCR（调用项目已有的 OCR 服务）
    # ==================================================================

    def _try_ocr_poster(self, image_url: str) -> str | None:
        """尝试下载海报图片并调用 OCR 识别。

        Args:
            image_url: 海报图片的完整 URL

        Returns:
            识别到的文本内容；失败返回 None
        """
        try:
            print(f"  -> [OCR] 下载海报图片: {image_url[:80]}...")
            resp = requests.get(
                image_url,
                headers=self._headers,
                timeout=30,
            )
            resp.raise_for_status()
            img_bytes = resp.content
            if not img_bytes or len(img_bytes) < 100:
                print(f"  -> [OCR] 图片内容过小 ({len(img_bytes)} 字节)，跳过")
                return None
            print(f"  -> [OCR] 图片下载成功 ({len(img_bytes)} 字节)，开始识别...")

            # 调用项目已有的 OCR 服务
            from app.services.activity_ocr_service import recognize_activity_image

            ocr_result = recognize_activity_image(
                filename="poster.png",
                content=img_bytes,
            )
            raw_text = ocr_result.get("raw_text", "")
            if raw_text:
                print(f"  -> [OCR] 识别成功 ({len(raw_text)} 字符)")
                return raw_text
            else:
                print(f"  -> [OCR] 识别结果为空")
                return None

        except ImportError:
            print("  -> [OCR] activity_ocr_service 模块不可用，跳过 OCR")
            return None
        except Exception as exc:
            print(f"  -> [OCR] 识别失败: {exc}")
            return None


# ============================================================================
# 模块级入口（供 crawler_service 通过注册表调用）
# ============================================================================

# 单例，避免每次调用都创建新实例
_spider_instance: CSEZJUSpider | None = None


def _get_spider() -> CSEZJUSpider:
    """获取 CSEZJUSpider 单例。"""
    global _spider_instance
    if _spider_instance is None:
        _spider_instance = CSEZJUSpider()
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
    CSEZJUSpider().main()
