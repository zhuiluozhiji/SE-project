"""爬虫基类 —— 所有学院/页面爬虫的公共抽象。

提供：
- 通用 HTTP 请求、编码检测
- 正文字段智能抽取（时间、主讲人、地点、主办方、类别）
- 总结/公示类内容过滤
- 年份过滤
- 翻页抓取 + 逐条详情 + 入库的完整编排流程
- 数据库写入与去重

子类只需实现两个方法：
    parse_activity_list(html)  → 从列表页 HTML 提取 [{title, detail_url, published_date}]
    parse_detail_page(html, detail_url) → 从详情页 HTML 提取 CrawledActivity
"""

from __future__ import annotations

import re
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


# ============================================================================
# 数据模型
# ============================================================================


@dataclass
class CrawledActivity:
    """所有爬虫统一的活动数据结构。"""
    title: str
    source_url: str
    published_date: str | None = None
    description: str | None = None
    author: str | None = None
    speaker: str | None = None
    start_time: str | None = None
    end_time: str | None = None
    location: str | None = None
    campus: str | None = None
    category: str | None = None
    organizer: str | None = None
    college: str | None = None
    skip: bool = False
    skip_reason: str = ""


# ============================================================================
# 通用常量（子类可覆盖）
# ============================================================================

# 模拟浏览器 UA
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}

# 已知浙大校区列表
ZJU_CAMPUSES = ["紫金港", "玉泉", "西溪", "华家池", "之江", "舟山", "海宁", "国际联合学院"]

# 标题中出现这些词 → 总结/公示类，直接跳过
SUMMARY_TITLE_KEYWORDS = [
    "顺利召开", "圆满结束", "圆满落幕", "圆满成功", "成功举办",
    "顺利举行", "成功举行", "圆满举行", "顺利闭幕", "胜利闭幕",
    "总结", "回顾", "结项", "公示", "获奖", "表彰",
    "结果", "名单", "评审", "评定", "考核", "验收",
    "计次", "打卡", "次数",
]

# 标题中出现这些词 → 更可能是活动/讲座/赛事通知，保留
EVENT_TITLE_KEYWORDS = [
    "讲座", "报告", "论坛", "沙龙", "研讨会", "工作坊", " Workshop",
    "竞赛", "比赛", "大赛", "挑战赛", "选拔赛",
    "活动", "实践", "实训", "训练营", "夏令营", "冬令营",
    "招募", "报名", "选拔", "挂职", "实习",
    "通知", "公告", "邀请",
]

# 正文中出现这些模式 → 总结/回顾类
SUMMARY_CONTENT_PATTERNS: list[tuple[str, str]] = [
    (r"(?:顺利|圆满|胜利|成功)\s*(?:召开|结束|落幕|举行|举办|完成|闭幕)", "正文含「顺利/圆满召开/结束」等表述"),
    (r"本次\s*(?:活动|讲座|会议|论坛|竞赛|比赛).{0,10}(?:顺利|圆满|成功|完美)", "正文含活动总结表述"),
    (r"(?:活动|讲座|会议|论坛)\s*(?:总结|回顾|复盘)", "正文含总结/回顾"),
    (r"(?:获奖|表彰)\s*(?:名单|情况|公示|结果)", "正文含获奖/表彰公示"),
    (r"公示\s*(?:期|时间|名单|结果)", "正文含公示信息"),
    (r"(?:经|经过|通过)\s*(?:评审|评选|考核|评定|审核)", "正文含评审/考核结果表述"),
    (r"(?:现将|现对|现就).{0,10}(?:公示|公布|通报)", "正文含结果公示表述"),
    (r"结项\s*(?:公示|审核|答辩|报告|总结)", "正文含结项内容"),
    (r"(?:附件|附)\s*[：:].{0,10}(?:名单|公示|结果)", "正文含附件公示"),
]


# ============================================================================
# 基类
# ============================================================================


class BaseSpider(ABC):
    """爬虫基类。

    子类必须定义：
        source: str       — 唯一来源标识，如 "cs_zju"
        college: str      — 学院/单位名称

    子类可选覆盖：
        base_url, list_url, list_pattern, max_pages
        min_year, headers, request_interval, request_timeout
    """

    # ---- 子类必须定义 ----
    source: str
    college: str

    # ---- 子类可选覆盖（URL / 翻页配置） ----
    base_url: str = ""
    list_url: str = ""
    list_pattern: str = ""        # 如 "/27181/list{page}.htm"，空字符串表示不翻页
    max_pages: int = 15

    # ---- 子类可选覆盖（过滤配置） ----
    min_year: int | None = 2026   # 默认仅保留 >= 此年份的活动（since 未传时生效），None 不过滤

    # ---- 子类可选覆盖（HTTP 配置） ----
    headers: dict | None = None   # None 表示使用 DEFAULT_HEADERS
    request_interval: float = 0.5
    request_timeout: int = 20

    # ---- 子类可选覆盖（关键词配置） ----
    summary_title_keywords: list[str] | None = None
    event_title_keywords: list[str] | None = None
    summary_content_patterns: list[tuple[str, str]] | None = None

    # ==================================================================
    # 抽象方法 —— 子类必须实现（网站 HTML 结构相关）
    # ==================================================================

    @abstractmethod
    def parse_activity_list(self, html: str) -> list[dict]:
        """从列表页 HTML 中提取活动条目。

        Args:
            html: 列表页 HTML 源码

        Returns:
            [{"title": str, "detail_url": str, "published_date": str | None}, ...]
        """
        ...

    @abstractmethod
    def parse_detail_page(self, html: str, detail_url: str) -> CrawledActivity:
        """从详情页 HTML 中提取活动信息。

        子类应在此方法中：
        1. 用 BeautifulSoup + CSS 选择器提取 title、description、author、published_date
        2. 调用 self._extract_structured_fields(title, description, published_date)
           获取 speaker、start_time、end_time、location、campus、organizer、category
        3. 调用 self._check_skip(title, description) 判断是否跳过
        4. 组装并返回 CrawledActivity

        Args:
            html: 详情页 HTML 源码
            detail_url: 详情页 URL

        Returns:
            CrawledActivity 实例
        """
        ...

    # ==================================================================
    # 属性访问器（支持子类覆盖配置）
    # ==================================================================

    @property
    def _headers(self) -> dict:
        return self.headers if self.headers is not None else DEFAULT_HEADERS

    @property
    def _summary_title_kw(self) -> list[str]:
        return self.summary_title_keywords if self.summary_title_keywords is not None else SUMMARY_TITLE_KEYWORDS

    @property
    def _event_title_kw(self) -> list[str]:
        return self.event_title_keywords if self.event_title_keywords is not None else EVENT_TITLE_KEYWORDS

    @property
    def _summary_content_pats(self) -> list[tuple[str, str]]:
        return self.summary_content_patterns if self.summary_content_patterns is not None else SUMMARY_CONTENT_PATTERNS

    # ==================================================================
    # HTTP 工具
    # ==================================================================

    def fetch_html(self, url: str, timeout: int | None = None) -> str:
        """获取网页 HTML 源码，自动处理中文编码。

        优先从 HTML <meta charset> 中检测编码，
        避免依赖服务器返回的 Content-Type（可能缺失 charset 导致乱码）。
        """
        if timeout is None:
            timeout = self.request_timeout
        response = requests.get(url, headers=self._headers, timeout=timeout)
        response.raise_for_status()
        raw = response.content

        meta_match = re.search(
            rb'<meta[^>]+charset[="\s]*([^"\s;/>]+)',
            raw[:2048],
            re.IGNORECASE,
        )
        if meta_match:
            encoding = meta_match.group(1).decode("ascii", errors="ignore")
        else:
            encoding = response.encoding or response.apparent_encoding or "utf-8"

        return raw.decode(encoding, errors="replace")

    # ==================================================================
    # 列表翻页（通用实现，适用于 /list{page}.htm 模式）
    # ==================================================================

    def crawl_all_list_pages(self, since: str | None = None) -> list[dict]:
        """翻页抓取所有列表页，返回全部活动条目（已去重，按日期倒序）。

        如果 self.list_pattern 为空字符串，则仅抓取 self.list_url 单页。

        Args:
            since: "YYYY-MM" 月份过滤，仅保留此月及之后的活动。
                   传入后会在列表阶段即过滤，遇到整页无符合条件条目时提前停止翻页。
        """
        all_items: list[dict] = []
        seen_urls: set[str] = set()
        errors: list[str] = []
        since_skipped_total = 0

        for page in range(1, self.max_pages + 1):
            if page == 1 or not self.list_pattern:
                url = self.list_url
            else:
                url = f"{self.base_url}{self.list_pattern.format(page=page)}"

            print(f"[列表] 正在抓取第 {page} 页: {url}")
            try:
                html = self.fetch_html(url)
                items = self.parse_activity_list(html)
                raw_count = len(items)

                # ---- 月份过滤：在列表阶段就剔除过期条目 ----
                if since:
                    items = [
                        item for item in items
                        if not self._is_before_since(item.get("published_date"), since)
                    ]
                    filtered_out = raw_count - len(items)
                    since_skipped_total += filtered_out
                    if filtered_out > 0:
                        print(f"  -> [月份过滤] 本页剔除 {filtered_out} 条早于 {since} 的条目")

                new_count = 0
                for item in items:
                    if item["detail_url"] not in seen_urls:
                        seen_urls.add(item["detail_url"])
                        all_items.append(item)
                        new_count += 1
                print(f"  -> 本页 {raw_count} 条，新增 {new_count} 条")

                # 整页无符合时间范围的新条目 → 后续页更旧，停止翻页
                if new_count == 0 and page > 1:
                    if since:
                        print(f"  -> 本页无符合 {since} 及之后的条目，停止翻页")
                    else:
                        print("  -> 无新条目，停止翻页")
                    break
            except Exception as exc:
                msg = f"第 {page} 页抓取失败: {exc}"
                print(f"  -> {msg}")
                errors.append(msg)
                if page == 1:
                    print(f"  -> 首页抓取失败，终止翻页。请检查网络和 URL: {url}")
                    break
                continue

            # 单页模式（无翻页模板）时只抓首页
            if not self.list_pattern:
                break

            if page < self.max_pages:
                time.sleep(self.request_interval)

        if errors:
            print(f"\n翻页过程中共 {len(errors)} 个错误:")
            for e in errors:
                print(f"  - {e}")

        if since and since_skipped_total > 0:
            print(f"\n[月份过滤] 列表阶段共剔除 {since_skipped_total} 条早于 {since} 的条目")

        all_items.sort(key=lambda x: x.get("published_date") or "", reverse=True)
        return all_items

    # ==================================================================
    # 详情页抓取
    # ==================================================================

    def crawl_detail_page(self, detail_url: str) -> CrawledActivity:
        """抓取单个详情页。"""
        html = self.fetch_html(detail_url)
        return self.parse_detail_page(html, detail_url)

    # ==================================================================
    # 结构化字段抽取（基于正文文本的正则匹配，跨网站通用）
    # ==================================================================

    def _extract_structured_fields(
        self, title: str, description: str, published_date: str | None,
    ) -> dict:
        """从标题+正文中抽取结构化字段。

        子类的 parse_detail_page 应在提取到 title/description/published_date 后
        调用此方法，获取其余字段。

        Returns:
            包含 speaker, start_time, end_time, location, campus,
            organizer, category 的字典
        """
        body_text = f"{title}\n{description}"

        start_time, end_time = self._extract_time_fields(body_text)
        start_time = self._fill_year(start_time, published_date)
        end_time = self._fill_year(end_time, published_date)

        speaker = self._extract_speaker(body_text)
        location, campus = self._extract_location(body_text)
        organizer = self._extract_organizer(body_text)
        category = self._infer_category(title, body_text)

        return {
            "speaker": speaker,
            "start_time": start_time,
            "end_time": end_time,
            "location": location,
            "campus": campus,
            "organizer": organizer,
            "category": category,
        }

    # ------------------------------------------------------------------
    # 时间字段提取
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_time_fields(text: str) -> tuple[str | None, str | None]:
        """从正文中提取开始时间和结束时间。

        支持的格式：
        - 2026年5月10日 14:00-16:00
        - 2026年5月10日14:00
        - 5月10日 14:00-16:00（无年份）
        - 5月10日 14:00（无年份）
        """
        # 模式1: "YYYY年M月D日 HH:MM-HH:MM"
        m = re.search(
            r"(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日[^\d]*"
            r"(\d{1,2}):(\d{2})\s*[-—~至到]\s*(\d{1,2}):(\d{2})",
            text,
        )
        if m:
            y, mo, d, h1, mi1, h2, mi2 = m.groups()
            return (
                f"{y}-{int(mo):02d}-{int(d):02d} {int(h1):02d}:{mi1}",
                f"{y}-{int(mo):02d}-{int(d):02d} {int(h2):02d}:{mi2}",
            )

        # 模式2: "YYYY年M月D日 HH:MM"（仅开始时间）
        m = re.search(
            r"(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日[^\d]*"
            r"(\d{1,2}):(\d{2})",
            text,
        )
        if m:
            y, mo, d, h1, mi1 = m.groups()
            return (f"{y}-{int(mo):02d}-{int(d):02d} {int(h1):02d}:{mi1}", None)

        # 模式3: "M月D日 HH:MM-HH:MM"（无年份）
        m = re.search(
            r"(\d{1,2})\s*月\s*(\d{1,2})\s*日[^\d]*"
            r"(\d{1,2}):(\d{2})\s*[-—~至到]\s*(\d{1,2}):(\d{2})",
            text,
        )
        if m:
            mo, d, h1, mi1, h2, mi2 = m.groups()
            return (
                f"****-{int(mo):02d}-{int(d):02d} {int(h1):02d}:{mi1}",
                f"****-{int(mo):02d}-{int(d):02d} {int(h2):02d}:{mi2}",
            )

        # 模式4: "M月D日 HH:MM"（无年份）
        m = re.search(
            r"(\d{1,2})\s*月\s*(\d{1,2})\s*日[^\d]*"
            r"(\d{1,2}):(\d{2})",
            text,
        )
        if m:
            mo, d, h1, mi1 = m.groups()
            return (f"****-{int(mo):02d}-{int(d):02d} {int(h1):02d}:{mi1}", None)

        return None, None

    @staticmethod
    def _fill_year(time_str: str | None, published_date: str | None) -> str | None:
        """用发布日期填充时间字符串中的年份占位符。"""
        if time_str is None:
            return None
        if "****" in time_str and published_date:
            year = published_date[:4]
            return time_str.replace("****", year)
        return time_str if "****" not in time_str else None

    @staticmethod
    def _normalize_datetime(time_str: str | None) -> datetime | None:
        """将多种日期时间字符串统一转换为 datetime 对象。"""
        if not time_str:
            return None
        formats = [
            "%Y-%m-%d %H:%M",
            "%Y-%m-%dT%H:%M",
            "%Y-%m-%d",
            "%Y年%m月%d日 %H:%M",
            "%Y年%m月%d日",
        ]
        for fmt in formats:
            try:
                return datetime.strptime(time_str, fmt)
            except ValueError:
                continue
        try:
            return datetime.fromisoformat(time_str)
        except ValueError:
            return None

    # ------------------------------------------------------------------
    # 主讲人提取
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_speaker(text: str) -> str | None:
        """提取主讲人/嘉宾/报告人。"""
        patterns = [
            r"主讲人[：:]\s*(.+?)(?:[，,。\n]|$)",
            r"嘉宾[：:]\s*(.+?)(?:[，,。\n]|$)",
            r"报告人[：:]\s*(.+?)(?:[，,。\n]|$)",
            r"分享嘉宾[：:]\s*(.+?)(?:[，,。\n]|$)",
            r"主讲[：:]\s*(.+?)(?:[，,。\n]|$)",
            r"演讲人[：:]\s*(.+?)(?:[，,。\n]|$)",
            r"授课人[：:]\s*(.+?)(?:[，,。\n]|$)",
            r"([^\s，,。\n]{2,4})\s*教授\s*(?:主讲|报告|分享|讲座|授课)",
        ]
        for pat in patterns:
            m = re.search(pat, text)
            if m:
                speaker = m.group(1).strip()
                speaker = re.sub(r"\s*(教授|博士|先生|女士|老师)?\s*$", "", speaker)
                if 2 <= len(speaker) <= 30:
                    return speaker
        return None

    # ------------------------------------------------------------------
    # 地点提取
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_location(text: str) -> tuple[str | None, str | None]:
        """提取地点和校区。"""
        location = None
        campus = None

        loc_patterns = [
            r"地点[：:]\s*(.+?)(?:[，,。\n]|$)",
            r"活动地点[：:]\s*(.+?)(?:[，,。\n]|$)",
            r"讲座地点[：:]\s*(.+?)(?:[，,。\n]|$)",
            r"举办地点[：:]\s*(.+?)(?:[，,。\n]|$)",
            r"会议地点[：:]\s*(.+?)(?:[，,。\n]|$)",
            r"上课地点[：:]\s*(.+?)(?:[，,。\n]|$)",
            r"地点[：:]\s*(.+?)$",
        ]
        for pat in loc_patterns:
            m = re.search(pat, text)
            if m:
                location = m.group(1).strip()
                if len(location) > 100:
                    location = location[:100]
                break

        search_text = f"{location or ''} {text}"
        for c in ZJU_CAMPUSES:
            if c in search_text:
                campus = c
                break

        return location, campus

    # ------------------------------------------------------------------
    # 主办方提取
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_organizer(text: str) -> str | None:
        """提取主办/承办单位。"""
        patterns = [
            r"主办[单位方]?[：:]\s*(.+?)(?:[，,。\n]|$)",
            r"承办[单位方]?[：:]\s*(.+?)(?:[，,。\n]|$)",
            r"组织单位[：:]\s*(.+?)(?:[，,。\n]|$)",
            r"协办[单位方]?[：:]\s*(.+?)(?:[，,。\n]|$)",
        ]
        for pat in patterns:
            m = re.search(pat, text)
            if m:
                org = m.group(1).strip()
                if len(org) >= 2:
                    return org
        return None

    # ------------------------------------------------------------------
    # 类别推断
    # ------------------------------------------------------------------

    @staticmethod
    def _infer_category(title: str, text: str) -> str | None:
        """从标题和正文推断活动类别。"""
        combined = f"{title} {text}"
        if any(kw in combined for kw in ["讲座", "报告", "论坛", "沙龙"]):
            return "讲座"
        if any(kw in combined for kw in ["竞赛", "比赛", "大赛", "挑战赛"]):
            return "竞赛"
        if any(kw in combined for kw in ["实践", "挂职", "实习", "实训", "志愿者"]):
            return "社会实践"
        if any(kw in combined for kw in ["研讨会", "工作坊", " Workshop"]):
            return "工作坊"
        if any(kw in combined for kw in ["文体", "体育", "运动会", "文艺", "晚会"]):
            return "文体活动"
        if any(kw in combined for kw in ["SQTP", "素质训练"]):
            return "SQTP"
        if any(kw in combined for kw in ["形势与政策", "形策"]):
            return "形势与政策"
        return "其他"

    # ==================================================================
    # 过滤逻辑
    # ==================================================================

    def should_skip_by_title(self, title: str) -> tuple[bool, str]:
        """根据标题判断是否应跳过该条目。"""
        for kw in self._summary_title_kw:
            if kw in title:
                return True, f"标题含总结关键词「{kw}」"

        for kw in self._event_title_kw:
            if kw in title:
                return False, ""

        return False, ""

    def _is_summary_content(self, title: str, description: str) -> tuple[bool, str]:
        """根据标题+正文内容判断是否为总结/回顾类文章。"""
        combined = f"{title} {description or ''}"

        for pattern, reason in self._summary_content_pats:
            if re.search(pattern, combined):
                return True, reason

        for kw in self._summary_title_kw:
            if kw in title:
                return True, f"标题含「{kw}」"

        return False, ""

    def _check_skip(self, title: str, description: str) -> tuple[bool, str]:
        """综合判断是否跳过（标题 + 正文内容）。"""
        skip, reason = self.should_skip_by_title(title)
        if not skip:
            skip, reason = self._is_summary_content(title, description)
        return skip, reason

    # ==================================================================
    # 时间过滤（年份 / 月份）
    # ==================================================================

    @staticmethod
    def _is_before_since(published_date: str | None, since: str | None) -> bool:
        """判断发布日期是否早于指定月份。

        Args:
            published_date: "YYYY-MM-DD" 格式的日期字符串
            since: "YYYY-MM" 格式的月份字符串

        Returns:
            True 表示应被过滤掉（早于 since 月）
        """
        if since is None or not published_date:
            return False
        try:
            return published_date[:7] < since
        except (TypeError, IndexError):
            return False

    def is_before_min_year(self, published_date: str | None) -> bool:
        """判断发布日期是否早于 min_year（since 未传时的兜底过滤）。"""
        if self.min_year is None:
            return False
        if not published_date:
            return False
        try:
            year = int(published_date[:4])
            return year < self.min_year
        except (ValueError, TypeError):
            return False

    def _resolve_since(self, since: str | None) -> str | None:
        """解析最终生效的 since 值：前端传入优先，否则回退到 min_year。"""
        if since is not None:
            return since
        if self.min_year is not None:
            return f"{self.min_year}-01"
        return None

    # ==================================================================
    # 数据库写入
    # ==================================================================

    def save_activities_to_db(
        self,
        activities: list[CrawledActivity],
        db_session,  # SQLAlchemy Session
        since: str | None = None,
    ) -> dict:
        """将爬取结果写入数据库（自动跳过标记为 skip 的条目）。

        去重策略：按 source_url 判断是否已存在。
        月份过滤已在列表阶段完成，此处仅做兜底校验。
        """
        from sqlalchemy import select

        from app.models.activity import Activity
        from app.models.crawl_record import CrawlRecord

        created = 0
        skipped_dup = 0
        skipped_filter = 0
        skipped_year = 0

        for a in activities:
            if a.skip:
                skipped_filter += 1
                print(f"  [过滤] {a.skip_reason}: {a.title[:50]}")
                continue

            # 兜底校验：如果既没有前端 since 也没有 min_year，则跳过
            # 正常情况下此检查不会触发（列表阶段已过滤）
            effective_since = self._resolve_since(since)
            if effective_since and self._is_before_since(a.published_date, effective_since):
                skipped_year += 1
                print(f"  [月份兜底] {a.published_date} 早于 {effective_since}: {a.title[:50]}")
                continue

            existing = db_session.scalar(
                select(Activity).where(Activity.source_url == a.source_url)
            )
            if existing is not None:
                skipped_dup += 1
                continue

            activity = Activity(
                title=a.title or "未命名活动",
                description=a.description,
                speaker=a.speaker,
                organizer=a.organizer,
                college=a.college or self.college,
                category=a.category,
                campus=a.campus,
                location=a.location,
                start_time=self._normalize_datetime(a.start_time),
                end_time=self._normalize_datetime(a.end_time),
                source_url=a.source_url,
                source_type="crawled",
                hot_score=0,
                status="open",
            )
            db_session.add(activity)
            created += 1

        db_session.commit()

        record = CrawlRecord(
            source=self.source,
            status="success",
            fetched_count=len(activities),
            success_count=created,
            error_msg=(
                f"filtered={skipped_filter}, month_skipped={skipped_year}, dup_skipped={skipped_dup}"
                if (skipped_filter or skipped_year or skipped_dup)
                else None
            ),
        )
        db_session.add(record)
        db_session.commit()

        return {
            "fetched": len(activities),
            "created": created,
            "skipped": skipped_dup,
            "filtered": skipped_filter,
            "year_filtered": skipped_year,
        }

    # ==================================================================
    # 主流程编排
    # ==================================================================

    def crawl_and_save(self, db_session, since: str | None = None) -> dict:
        """完整爬取流程：列表翻页 → 逐条详情 → 过滤 → 写入数据库。

        Args:
            db_session: SQLAlchemy 数据库会话
            since: "YYYY-MM" 月份过滤，仅爬取此月及之后的活动。
                   None 时自动回退到 self.min_year。
        """
        # 解析最终生效的 since
        effective_since = self._resolve_since(since)

        print("=" * 60)
        print(f"开始爬取 {self.college} - {self.source}")
        if effective_since:
            print(f"月份过滤: 仅保留 >= {effective_since} 的活动")
        print("=" * 60)

        # 0. 连通性检查
        print(f"[检查] 测试连通性: {self.list_url}")
        try:
            test_html = self.fetch_html(self.list_url)
            if not test_html or len(test_html) < 500:
                return {
                    "status": "error",
                    "fetched": 0, "created": 0, "skipped": 0,
                    "filtered": 0, "year_filtered": 0,
                    "since_applied": effective_since,
                    "error": f"列表页返回内容过短 ({len(test_html)} 字符)，可能被拦截或重定向",
                }
            print(f"  -> 连通性 OK，页面长度 {len(test_html)} 字符")
        except Exception as exc:
            return {
                "status": "error",
                "fetched": 0, "created": 0, "skipped": 0,
                "filtered": 0, "year_filtered": 0,
                "since_applied": effective_since,
                "error": f"无法访问列表页: {exc}",
            }

        # 1. 翻页抓取列表（已在内部按 since 过滤，提前停止翻页）
        list_items = self.crawl_all_list_pages(since=effective_since)
        print(f"\n共获取 {len(list_items)} 个活动条目\n")

        if not list_items:
            return {
                "status": "empty",
                "fetched": 0, "created": 0, "skipped": 0,
                "filtered": 0, "year_filtered": 0,
                "error": "列表页解析结果为空，可能页面结构已变更",
            }

        if not list_items:
            return {
                "status": "empty",
                "fetched": 0, "created": 0, "skipped": 0,
                "filtered": 0, "year_filtered": 0,
                "since_applied": effective_since,
                "error": "列表页解析结果为空，可能页面结构已变更",
            }

        # 2. 逐条抓取详情（过期条目已在列表阶段剔除，此处不再重复过滤）
        activities: list[CrawledActivity] = []
        for i, item in enumerate(list_items, 1):
            print(f"[详情 {i}/{len(list_items)}] {item['title'][:50]}...")
            try:
                activity = self.crawl_detail_page(item["detail_url"])
                if item.get("published_date") and not activity.published_date:
                    activity.published_date = item["published_date"]
                activities.append(activity)

                if activity.skip:
                    print(f"  -> ⏭ 跳过 | {activity.skip_reason}")
                else:
                    parts = []
                    if activity.published_date:
                        parts.append(f"日期: {activity.published_date}")
                    if activity.speaker:
                        parts.append(f"主讲: {activity.speaker}")
                    if activity.location:
                        parts.append(f"地点: {activity.location}")
                    if activity.category:
                        parts.append(f"类别: {activity.category}")
                    print(f"  -> ✓ | {' | '.join(parts)}")
            except Exception as exc:
                print(f"  -> ✗ 失败: {exc}")
                activities.append(CrawledActivity(
                    title=item["title"],
                    source_url=item["detail_url"],
                    published_date=item.get("published_date"),
                ))
            time.sleep(self.request_interval)

        kept = [a for a in activities if not a.skip]
        print(
            f"\n详情抓取完成：总计 {len(activities)} 条，"
            f"保留 {len(kept)} 条，过滤 {len(activities) - len(kept)} 条"
        )

        # 3. 写入数据库
        result = self.save_activities_to_db(activities, db_session, since=effective_since)
        result["since_applied"] = effective_since
        print(
            f"\n入库结果：抓取 {result['fetched']} 条，"
            f"新增 {result['created']} 条，"
            f"去重跳过 {result['skipped']} 条，"
            f"内容过滤 {result['filtered']} 条，"
            f"月份过滤 {result.get('year_filtered', 0)} 条"
        )
        return {"status": "success", **result}

    # ==================================================================
    # 命令行入口（仅打印，不写库）
    # ==================================================================

    def main(self) -> None:
        """命令行直接运行：仅打印列表，不写库。"""
        print("=" * 60)
        print(f"{self.college} 活动爬虫（仅打印模式）")
        print("=" * 60)

        list_items = self.crawl_all_list_pages()
        print(f"\n共获取 {len(list_items)} 个活动条目\n")

        for item in list_items:
            print(
                f"日期: {item.get('published_date', '未知')} | "
                f"标题: {item['title']} | "
                f"链接: {item['detail_url']}"
            )

        print("\n" + "=" * 60)
        print("提示：使用 spider.crawl_and_save(db) 可完整抓取并入库")
        print("=" * 60)
