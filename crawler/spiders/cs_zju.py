"""CS ZJU 学院官网学生活动爬虫。

功能：
- 翻页抓取全部列表页（/27181/list.htm 至 list15.htm）
- 逐条进入详情页提取正文内容
- 从正文中智能抽取结构化字段（时间、地点、主讲人、主办方、校区、类别）
- 过滤总结/公示/回顾类帖子，仅保留活动、赛事、讲座通知
- 支持将结果写入数据库
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass
from datetime import datetime
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

BASE_URL = "http://cspo.zju.edu.cn"
LIST_URL = f"{BASE_URL}/27181/list.htm"
LIST_PATTERN = "/27181/list{page}.htm"
MAX_PAGES = 15
REQUEST_INTERVAL = 0.5  # 请求间隔（秒），避免对服务器造成压力
REQUEST_TIMEOUT = 20    # 请求超时（秒）

# ---------------------------------------------------------------------------
# 年份过滤器（模块化，修改此值即可调整入库年份范围）
# ---------------------------------------------------------------------------
# 仅保留发布日期 >= MIN_YEAR 的活动。设为 None 则不过滤。
MIN_YEAR: int | None = 2026

# 模拟浏览器，避免被服务器拒绝
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}

# ---------------------------------------------------------------------------
# 已知校区列表（用于正文匹配）
# ---------------------------------------------------------------------------
ZJU_CAMPUSES = ["紫金港", "玉泉", "西溪", "华家池", "之江", "舟山", "海宁", "国际联合学院"]

# ---------------------------------------------------------------------------
# 过滤关键词
# ---------------------------------------------------------------------------

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

# ---------------------------------------------------------------------------
# 数据模型
# ---------------------------------------------------------------------------


@dataclass
class CrawledActivity:
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
    # 标记是否应跳过（总结/公示类）
    skip: bool = False
    skip_reason: str = ""


# ---------------------------------------------------------------------------
# HTTP 工具
# ---------------------------------------------------------------------------


def fetch_html(url: str, timeout: int = REQUEST_TIMEOUT) -> str:
    """获取网页 HTML 源码，自动处理中文编码。

    优先从 HTML <meta charset> 中检测编码，
    避免依赖服务器返回的 Content-Type（可能缺失 charset 导致乱码）。
    """
    response = requests.get(url, headers=HEADERS, timeout=timeout)
    response.raise_for_status()
    raw = response.content

    # 从 HTML meta 标签中检测编码
    meta_match = re.search(
        rb'<meta[^>]+charset[="\s]*([^"\s;/>]+)',
        raw[:2048],
        re.IGNORECASE,
    )
    if meta_match:
        encoding = meta_match.group(1).decode("ascii", errors="ignore")
    else:
        # 回退：优先服务器声明的编码，再试 chardet-style 猜测
        encoding = response.encoding or response.apparent_encoding or "utf-8"

    return raw.decode(encoding, errors="replace")


# ---------------------------------------------------------------------------
# 列表页解析
# ---------------------------------------------------------------------------


def parse_activity_list(html: str) -> list[dict]:
    """从列表页 HTML 中提取所有活动的标题、链接和发布日期。"""
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
            "detail_url": urljoin(BASE_URL, href),
            "published_date": date_text,
        })

    return items


def crawl_all_list_pages(max_pages: int = MAX_PAGES) -> list[dict]:
    """翻页抓取所有列表页，返回全部活动条目（已去重，按日期倒序）。"""
    all_items: list[dict] = []
    seen_urls: set[str] = set()
    errors: list[str] = []

    for page in range(1, max_pages + 1):
        if page == 1:
            url = LIST_URL
        else:
            url = f"{BASE_URL}{LIST_PATTERN.format(page=page)}"

        print(f"[列表] 正在抓取第 {page} 页: {url}")
        try:
            html = fetch_html(url)
            items = parse_activity_list(html)
            new_count = 0
            for item in items:
                if item["detail_url"] not in seen_urls:
                    seen_urls.add(item["detail_url"])
                    all_items.append(item)
                    new_count += 1
            print(f"  -> 本页 {len(items)} 条，新增 {new_count} 条")
            if new_count == 0 and page > 1:
                print("  -> 无新条目，停止翻页")
                break
        except Exception as exc:
            msg = f"第 {page} 页抓取失败: {exc}"
            print(f"  -> {msg}")
            errors.append(msg)
            if page == 1:
                # 第1页失败是致命错误
                print(f"  -> 首页抓取失败，终止翻页。请检查网络和 URL: {url}")
                break
            continue

        if page < max_pages:
            time.sleep(REQUEST_INTERVAL)

    if errors:
        print(f"\n翻页过程中共 {len(errors)} 个错误:")
        for e in errors:
            print(f"  - {e}")

    # 按发布日期倒序
    all_items.sort(key=lambda x: x.get("published_date") or "", reverse=True)
    return all_items


# ---------------------------------------------------------------------------
# 标题过滤
# ---------------------------------------------------------------------------


def should_skip_by_title(title: str) -> tuple[bool, str]:
    """根据标题判断是否应跳过该条目。

    Returns:
        (should_skip, reason): 是否跳过及原因
    """
    # 1. 检测总结/公示关键词
    for kw in SUMMARY_TITLE_KEYWORDS:
        if kw in title:
            return True, f"标题含总结关键词「{kw}」"

    # 2. 检测是否为活动/讲座/赛事类
    for kw in EVENT_TITLE_KEYWORDS:
        if kw in title:
            return False, ""

    # 3. 标题以【xxx】开头但无法归类 → 检查内容再决定
    #    先不跳过，等详情页解析后再判断
    return False, ""


# ---------------------------------------------------------------------------
# 年份过滤器（模块化：修改顶部 MIN_YEAR 即可调整）
# ---------------------------------------------------------------------------


def is_before_min_year(published_date: str | None) -> bool:
    """判断发布日期是否早于 MIN_YEAR。

    Args:
        published_date: 发布日期字符串，如 "2025-12-12"

    Returns:
        True 表示应被过滤掉（早于最小年份）
    """
    if MIN_YEAR is None:
        return False
    if not published_date:
        return False  # 无日期的不过滤，保留
    try:
        year = int(published_date[:4])
        return year < MIN_YEAR
    except (ValueError, TypeError):
        return False


# ---------------------------------------------------------------------------
# 详情页解析 —— 字段提取
# ---------------------------------------------------------------------------


def _extract_field(pattern: str, text: str, group: int = 1) -> str | None:
    """用正则从文本中提取单个字段。"""
    m = re.search(pattern, text)
    return m.group(group).strip() if m else None


def _extract_time_fields(text: str) -> tuple[str | None, str | None]:
    """从正文中提取开始时间和结束时间。

    常见格式：
    - 活动时间：2026年7月中旬-8月中旬，共4周
    - 时间：2026年5月10日（周日）14:00-16:00
    - 讲座时间：5月20日 14:00
    - 时间：2026年5月10日14:00
    """
    start_time = None
    end_time = None

    # 模式1: "YYYY年M月D日 HH:MM-HH:MM"
    m = re.search(
        r"(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日[^\d]*"
        r"(\d{1,2}):(\d{2})\s*[-—~至到]\s*(\d{1,2}):(\d{2})",
        text,
    )
    if m:
        y, mo, d, h1, mi1, h2, mi2 = m.groups()
        start_time = f"{y}-{int(mo):02d}-{int(d):02d} {int(h1):02d}:{mi1}"
        end_time = f"{y}-{int(mo):02d}-{int(d):02d} {int(h2):02d}:{mi2}"
        return start_time, end_time

    # 模式2: "YYYY年M月D日 HH:MM"（仅开始时间）
    m = re.search(
        r"(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日[^\d]*"
        r"(\d{1,2}):(\d{2})",
        text,
    )
    if m:
        y, mo, d, h1, mi1 = m.groups()
        start_time = f"{y}-{int(mo):02d}-{int(d):02d} {int(h1):02d}:{mi1}"
        return start_time, None

    # 模式3: "M月D日 HH:MM-HH:MM"（无年份，用发布日期推断）
    m = re.search(
        r"(\d{1,2})\s*月\s*(\d{1,2})\s*日[^\d]*"
        r"(\d{1,2}):(\d{2})\s*[-—~至到]\s*(\d{1,2}):(\d{2})",
        text,
    )
    if m:
        mo, d, h1, mi1, h2, mi2 = m.groups()
        # 年份稍后由发布日期补充
        start_time = f"****-{int(mo):02d}-{int(d):02d} {int(h1):02d}:{mi1}"
        end_time = f"****-{int(mo):02d}-{int(d):02d} {int(h2):02d}:{mi2}"
        return start_time, end_time

    # 模式4: "M月D日 HH:MM"（无年份）
    m = re.search(
        r"(\d{1,2})\s*月\s*(\d{1,2})\s*日[^\d]*"
        r"(\d{1,2}):(\d{2})",
        text,
    )
    if m:
        mo, d, h1, mi1 = m.groups()
        start_time = f"****-{int(mo):02d}-{int(d):02d} {int(h1):02d}:{mi1}"
        return start_time, None

    return None, None


def _fill_year(time_str: str | None, published_date: str | None) -> str | None:
    """用发布日期填充时间字符串中的年份占位符。"""
    if time_str is None:
        return None
    if "****" in time_str and published_date:
        year = published_date[:4]
        return time_str.replace("****", year)
    return time_str if "****" not in time_str else None


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
            # 清理常见后缀
            speaker = re.sub(r"\s*(教授|博士|先生|女士|老师)?\s*$", "", speaker)
            if len(speaker) >= 2 and len(speaker) <= 30:
                return speaker
    return None


def _extract_location(text: str) -> tuple[str | None, str | None]:
    """提取地点和校区。"""
    location = None
    campus = None

    # 提取地点
    loc_patterns = [
        r"地点[：:]\s*(.+?)(?:[，,。\n]|$)",
        r"活动地点[：:]\s*(.+?)(?:[，,。\n]|$)",
        r"讲座地点[：:]\s*(.+?)(?:[，,。\n]|$)",
        r"举办地点[：:]\s*(.+?)(?:[，,。\n]|$)",
        r"会议地点[：:]\s*(.+?)(?:[，,。\n]|$)",
        r"上课地点[：:]\s*(.+?)(?:[，,。\n]|$)",
        r"地点[：:]\s*(.+?)$",  # 行末
    ]
    for pat in loc_patterns:
        m = re.search(pat, text)
        if m:
            location = m.group(1).strip()
            # 截断过长的地点文本
            if len(location) > 100:
                location = location[:100]
            break

    # 从地点或正文中提取校区
    search_text = f"{location or ''} {text}"
    for c in ZJU_CAMPUSES:
        if c in search_text:
            campus = c
            break

    return location, campus


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


def _is_summary_content(title: str, description: str) -> tuple[bool, str]:
    """根据标题+正文内容判断是否为总结/回顾类文章。

    Returns:
        (is_summary, reason)
    """
    combined = f"{title} {description or ''}"

    # 正文中出现大量总结性词汇 → 总结文
    summary_patterns = [
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

    for pattern, reason in summary_patterns:
        if re.search(pattern, combined):
            return True, reason

    # 标题本身已含总结词（should_skip_by_title 已处理，此处兜底）
    for kw in SUMMARY_TITLE_KEYWORDS:
        if kw in title:
            return True, f"标题含「{kw}」"

    return False, ""


# ---------------------------------------------------------------------------
# 详情页解析（主函数）
# ---------------------------------------------------------------------------


def parse_detail_page(html: str, detail_url: str) -> CrawledActivity:
    """解析活动详情页，提取所有结构化字段。"""
    soup = BeautifulSoup(html, "html.parser")

    # --- 标题 ---
    title = ""
    title_el = soup.select_one("h1.wp_articleTitle, h1.arti_title, h1, .arti_title")
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

    # ==================================================================
    # 从正文中抽取结构化字段
    # ==================================================================
    body_text = f"{title}\n{description}"

    # 时间
    start_time, end_time = _extract_time_fields(body_text)
    start_time = _fill_year(start_time, published_date)
    end_time = _fill_year(end_time, published_date)

    # 主讲人
    speaker = _extract_speaker(body_text)

    # 地点 & 校区
    location, campus = _extract_location(body_text)

    # 主办方
    organizer = _extract_organizer(body_text)
    if organizer is None:
        # 默认用学院名
        organizer = "计算机科学与技术学院"

    # 类别推断
    category = _infer_category(title, body_text)

    # ==================================================================
    # 判断是否为总结/回顾类 → 标记跳过
    # ==================================================================
    skip, skip_reason = should_skip_by_title(title)
    if not skip:
        skip, skip_reason = _is_summary_content(title, description)

    return CrawledActivity(
        title=title,
        source_url=detail_url,
        published_date=published_date,
        description=description,
        author=author,
        speaker=speaker,
        start_time=start_time,
        end_time=end_time,
        location=location,
        campus=campus,
        category=category,
        organizer=organizer,
        college="计算机科学与技术学院",
        skip=skip,
        skip_reason=skip_reason,
    )


def crawl_detail_page(detail_url: str) -> CrawledActivity:
    """抓取单个详情页。"""
    html = fetch_html(detail_url)
    return parse_detail_page(html, detail_url)


# ---------------------------------------------------------------------------
# 数据库写入
# ---------------------------------------------------------------------------


def save_activities_to_db(
    activities: list[CrawledActivity],
    db_session,  # SQLAlchemy Session
) -> dict:
    """将爬取结果写入数据库（自动跳过 marked as skip 的条目）。

    去重策略：按 source_url 判断是否已存在。
    """
    from sqlalchemy import select

    from app.models.activity import Activity
    from app.models.crawl_record import CrawlRecord

    created = 0
    skipped_dup = 0
    skipped_filter = 0
    skipped_year = 0

    for a in activities:
        # 跳过总结/公示类
        if a.skip:
            skipped_filter += 1
            print(f"  [过滤] {a.skip_reason}: {a.title[:50]}")
            continue

        # 年份过滤：仅保留 MIN_YEAR 及之后的活动
        if is_before_min_year(a.published_date):
            skipped_year += 1
            print(f"  [年份] {a.published_date} 早于 {MIN_YEAR}: {a.title[:50]}")
            continue

        # 去重检查
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
            college=a.college or "计算机科学与技术学院",
            category=a.category,
            campus=a.campus,
            location=a.location,
            start_time=_normalize_datetime(a.start_time),
            end_time=_normalize_datetime(a.end_time),
            source_url=a.source_url,
            source_type="crawled",
            hot_score=0,
            status="open",
        )
        db_session.add(activity)
        created += 1

    db_session.commit()

    # 记录爬虫运行日志
    record = CrawlRecord(
        source="cs_zju",
        status="success",
        fetched_count=len(activities),
        success_count=created,
        error_msg=(
            f"filtered={skipped_filter}, year_skipped={skipped_year}, dup_skipped={skipped_dup}"
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


# ---------------------------------------------------------------------------
# 主入口
# ---------------------------------------------------------------------------


def crawl_and_save(db_session) -> dict:
    """完整爬取流程：列表翻页 → 逐条详情 → 过滤 → 写入数据库。"""
    print("=" * 60)
    print("开始爬取 CS ZJU 学生活动")
    print("=" * 60)

    # 0. 连通性检查
    print(f"[检查] 测试连通性: {LIST_URL}")
    try:
        test_html = fetch_html(LIST_URL)
        if not test_html or len(test_html) < 500:
            return {
                "status": "error",
                "fetched": 0, "created": 0, "skipped": 0, "filtered": 0, "year_filtered": 0,
                "error": f"列表页返回内容过短 ({len(test_html)} 字符)，可能被拦截或重定向",
            }
        print(f"  -> 连通性 OK，页面长度 {len(test_html)} 字符")
    except Exception as exc:
        return {
            "status": "error",
            "fetched": 0, "created": 0, "skipped": 0, "filtered": 0, "year_filtered": 0,
            "error": f"无法访问列表页: {exc}",
        }

    # 1. 翻页抓取列表
    list_items = crawl_all_list_pages()
    print(f"\n共获取 {len(list_items)} 个活动条目\n")

    if not list_items:
        return {
            "status": "empty",
            "fetched": 0, "created": 0, "skipped": 0, "filtered": 0, "year_filtered": 0,
            "error": "列表页解析结果为空，可能页面结构已变更",
        }

    # 2. 逐条抓取详情
    activities: list[CrawledActivity] = []
    for i, item in enumerate(list_items, 1):
        print(f"[详情 {i}/{len(list_items)}] {item['title'][:50]}...")
        try:
            activity = crawl_detail_page(item["detail_url"])
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
        time.sleep(REQUEST_INTERVAL)

    kept = [a for a in activities if not a.skip]
    print(
        f"\n详情抓取完成：总计 {len(activities)} 条，"
        f"保留 {len(kept)} 条，过滤 {len(activities) - len(kept)} 条"
    )

    # 3. 写入数据库
    result = save_activities_to_db(activities, db_session)
    print(
        f"\n入库结果：抓取 {result['fetched']} 条，"
        f"新增 {result['created']} 条，"
        f"去重跳过 {result['skipped']} 条，"
        f"内容过滤 {result['filtered']} 条，"
        f"年份过滤 {result.get('year_filtered', 0)} 条"
    )
    return {"status": "success", **result}


def main() -> None:
    """命令行直接运行：仅打印不写库。"""
    print("=" * 60)
    print("CS ZJU 学生活动爬虫（仅打印模式）")
    print("=" * 60)

    list_items = crawl_all_list_pages()
    print(f"\n共获取 {len(list_items)} 个活动条目\n")

    for item in list_items:
        print(
            f"日期: {item.get('published_date', '未知')} | "
            f"标题: {item['title']} | "
            f"链接: {item['detail_url']}"
        )

    # 也可选择抓取详情来测试过滤效果
    print("\n" + "=" * 60)
    print("提示：使用 crawl_and_save(db) 可完整抓取并入库")
    print("=" * 60)


if __name__ == "__main__":
    main()

