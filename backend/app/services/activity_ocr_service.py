from __future__ import annotations

import csv
import io
import os
import re
import shutil
import subprocess
import tempfile
from datetime import datetime, timedelta
from pathlib import Path


ALLOWED_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}
OCR_TIMEOUT_SECONDS = 12
MAX_ACTIVITY_SCREENSHOTS = 5
OCR_FULL_IMAGE_PSM_MODES = ("6", "11")
OCR_VARIANT_PSM_MODES = ("6",)
OCR_VERTICAL_PSM_MODES = ("5", "11")
OCR_TSV_PSM_MODES = ("11",)
OCR_LANG_DEFAULT = "chi_sim+eng"
OCR_LANG_VERTICAL = "chi_sim_vert+chi_sim+eng"
OCR_IMAGE_VARIANT_SPECS = (
    (
        "enhanced",
        ("-auto-orient", "-resize", "1800x1800", "-colorspace", "Gray", "-auto-level", "-sharpen", "0x1"),
    ),
    (
        "threshold",
        ("-auto-orient", "-resize", "1800x1800", "-colorspace", "Gray", "-auto-level", "-threshold", "55%"),
    ),
    (
        "right_crop",
        (
            "-auto-orient",
            "-gravity",
            "East",
            "-crop",
            "58%x100%+0+0",
            "+repage",
            "-resize",
            "2000x2000",
            "-colorspace",
            "Gray",
            "-auto-level",
            "-sharpen",
            "0x1",
        ),
    ),
    (
        "right_narrow_crop",
        (
            "-auto-orient",
            "-gravity",
            "East",
            "-crop",
            "42%x100%+0+0",
            "+repage",
            "-resize",
            "2000x2000",
            "-colorspace",
            "Gray",
            "-auto-level",
            "-sharpen",
            "0x1",
        ),
    ),
)
DECORATIVE_TITLE_WORDS = ("节目单", "海报", "通知", "公告", "邀请函", "预告")
ACTIVITY_TITLE_KEYWORDS = (
    "讲座",
    "报告",
    "论坛",
    "研讨",
    "工作坊",
    "沙龙",
    "分享会",
    "比赛",
    "大赛",
    "决赛",
    "复赛",
    "初赛",
    "音乐会",
    "晚会",
    "展览",
)


class ActivityOcrError(ValueError):
    """Base error for activity screenshot recognition."""


class OcrUnavailableError(ActivityOcrError):
    """Raised when the tesseract executable is not available."""


class OcrRecognitionError(ActivityOcrError):
    """Raised when tesseract cannot recognize the uploaded image."""


def recognize_activity_image(filename: str, content: bytes) -> dict:
    return recognize_activity_images([(filename, content)])


def recognize_activity_images(files: list[tuple[str, bytes]]) -> dict:
    if not files:
        raise ValueError("请至少上传一张活动截图。")
    if len(files) > MAX_ACTIVITY_SCREENSHOTS:
        raise ValueError(f"一个活动最多支持 {MAX_ACTIVITY_SCREENSHOTS} 张截图。")

    screenshot_results = []
    all_candidates: list[str] = []
    for filename, content in files:
        candidates = run_tesseract_image(filename=filename, content=content)
        if isinstance(candidates, str):
            candidates = [candidates]
        all_candidates.extend(candidates)
        screenshot_results.append(
            {
                "filename": filename,
                "raw_text": choose_display_text(candidates),
            }
        )

    all_candidates = dedupe_text_candidates(all_candidates)
    if not all_candidates:
        raise ValueError("未识别到可用文字，请换一张更清晰的截图。")

    combined_text = normalize_ocr_text(
        "\n".join(item["raw_text"] for item in screenshot_results if item["raw_text"])
    )
    activity = parse_activity_from_candidates(all_candidates)
    return {
        "filename": screenshot_results[0]["filename"],
        "filenames": [item["filename"] for item in screenshot_results],
        "raw_text": combined_text,
        "activity": activity,
        "warnings": build_parse_warnings(activity),
        "screenshots": screenshot_results,
    }


def run_tesseract_image(filename: str, content: bytes) -> list[str]:
    if not content:
        raise ValueError("图片内容为空，请重新上传。")

    suffix = Path(filename or "").suffix.lower() or ".png"
    if suffix not in ALLOWED_IMAGE_SUFFIXES:
        raise ValueError("图片格式不支持，请上传 PNG、JPG、WEBP、BMP 或 TIFF 格式。")

    tesseract = shutil.which("tesseract")
    if not tesseract:
        raise OcrUnavailableError("OCR 引擎未安装，请重新构建 backend 镜像后再试。")

    tmp_dir = ""
    try:
        tmp_dir = tempfile.mkdtemp(prefix="activity-ocr-")
        source_path = os.path.join(tmp_dir, f"source{suffix}")
        Path(source_path).write_bytes(content)

        results = []
        errors = []
        for image_path, variant_name in build_ocr_image_variants(source_path, tmp_dir):
            psm_modes = choose_psm_modes_for_variant(variant_name)
            for psm in psm_modes:
                result = run_tesseract_command(
                    tesseract,
                    image_path,
                    psm,
                    lang=choose_ocr_lang_for_variant(variant_name),
                )
                if result.returncode == 0:
                    raw_text = normalize_ocr_text(result.stdout)
                    if raw_text:
                        results.append(raw_text)
                else:
                    errors.append((result.stderr or "").strip())
            for psm in choose_tsv_modes_for_variant(variant_name):
                result = run_tesseract_command(
                    tesseract,
                    image_path,
                    psm,
                    output_format="tsv",
                    lang=choose_ocr_lang_for_variant(variant_name),
                )
                if result.returncode == 0:
                    results.extend(extract_text_candidates_from_tsv(result.stdout))
                else:
                    errors.append((result.stderr or "").strip())
    except subprocess.TimeoutExpired as exc:
        raise OcrRecognitionError("OCR 识别超时，请尝试裁剪截图后重新上传。") from exc
    finally:
        if tmp_dir:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    if not results:
        detail = next((error for error in errors if error), "")
        message = "OCR 识别失败，请确认截图清晰后重试。"
        if detail:
            message = f"{message}错误信息：{detail[:120]}"
        raise OcrRecognitionError(message)

    return dedupe_text_candidates(results)


def build_ocr_image_variants(source_path: str, tmp_dir: str) -> list[tuple[str, str]]:
    variants = [(source_path, "original")]
    if is_tesseract_language_available("chi_sim_vert"):
        variants.append((source_path, "vertical_original"))

    imagemagick = find_imagemagick_command()
    if not imagemagick:
        return variants

    for name, operations in OCR_IMAGE_VARIANT_SPECS:
        output_path = os.path.join(tmp_dir, f"{name}.png")
        result = subprocess.run(
            [imagemagick, source_path, *operations, output_path],
            capture_output=True,
            text=True,
            timeout=OCR_TIMEOUT_SECONDS,
            check=False,
        )
        if result.returncode == 0 and os.path.exists(output_path):
            variants.append((output_path, name))
    return variants


def find_imagemagick_command() -> str | None:
    return shutil.which("magick") or shutil.which("convert")


def choose_psm_modes_for_variant(variant_name: str) -> tuple[str, ...]:
    if variant_name == "original":
        return OCR_FULL_IMAGE_PSM_MODES
    if is_vertical_ocr_variant(variant_name):
        return OCR_VERTICAL_PSM_MODES
    return OCR_VARIANT_PSM_MODES


def choose_tsv_modes_for_variant(variant_name: str) -> tuple[str, ...]:
    if variant_name == "original" or is_vertical_ocr_variant(variant_name):
        return OCR_TSV_PSM_MODES
    return ()


def choose_ocr_lang_for_variant(variant_name: str) -> str:
    if is_vertical_ocr_variant(variant_name) and is_tesseract_language_available("chi_sim_vert"):
        return OCR_LANG_VERTICAL
    return OCR_LANG_DEFAULT


def is_vertical_ocr_variant(variant_name: str) -> bool:
    return variant_name in {"vertical_original", "right_crop", "right_narrow_crop"}


def is_tesseract_language_available(language: str) -> bool:
    tessdata_prefix = os.environ.get("TESSDATA_PREFIX")
    search_roots = []
    if tessdata_prefix:
        search_roots.append(Path(tessdata_prefix))
    search_roots.extend(
        [
            Path("/usr/share/tesseract-ocr/5/tessdata"),
            Path("/usr/share/tessdata"),
        ]
    )
    return any((root / f"{language}.traineddata").exists() for root in search_roots)


def run_tesseract_command(
    tesseract: str,
    image_path: str,
    psm: str,
    output_format: str | None = None,
    lang: str = OCR_LANG_DEFAULT,
) -> subprocess.CompletedProcess[str]:
    command = [
        tesseract,
        image_path,
        "stdout",
        "-l",
        lang,
        "--oem",
        "1",
        "--psm",
        psm,
        "-c",
        "preserve_interword_spaces=1",
    ]
    if output_format:
        command.append(output_format)
    return subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=OCR_TIMEOUT_SECONDS,
        check=False,
    )


def extract_text_candidates_from_tsv(tsv_text: str) -> list[str]:
    if not tsv_text:
        return []

    rows = []
    try:
        reader = csv.DictReader(io.StringIO(tsv_text), delimiter="\t")
        for row in reader:
            token = clean_ocr_token(row.get("text", ""))
            if not token:
                continue
            conf = parse_float(row.get("conf"), default=-1)
            if conf < 0:
                continue
            rows.append(
                {
                    "text": token,
                    "left": parse_int(row.get("left"), default=0),
                    "top": parse_int(row.get("top"), default=0),
                    "width": parse_int(row.get("width"), default=0),
                    "height": parse_int(row.get("height"), default=0),
                    "page_num": parse_int(row.get("page_num"), default=0),
                    "block_num": parse_int(row.get("block_num"), default=0),
                    "par_num": parse_int(row.get("par_num"), default=0),
                    "line_num": parse_int(row.get("line_num"), default=0),
                    "word_num": parse_int(row.get("word_num"), default=0),
                }
            )
    except csv.Error:
        return []

    vertical_text = build_vertical_text_from_ocr_words(rows)
    candidates = [
        build_text_by_tsv_lines(rows),
        vertical_text,
    ]
    if not vertical_text:
        candidates.append(build_text_by_top_left(rows))
    return dedupe_text_candidates(candidates)


def build_text_by_tsv_lines(rows: list[dict]) -> str:
    if not rows:
        return ""

    grouped: dict[tuple[int, int, int, int], list[dict]] = {}
    for row in rows:
        key = (row["page_num"], row["block_num"], row["par_num"], row["line_num"])
        grouped.setdefault(key, []).append(row)

    lines = []
    for group_rows in grouped.values():
        ordered_rows = sorted(group_rows, key=lambda item: (item["word_num"], item["left"]))
        line = join_ocr_tokens([item["text"] for item in ordered_rows])
        if line:
            lines.append((min(item["top"] for item in group_rows), min(item["left"] for item in group_rows), line))

    return normalize_ocr_text("\n".join(line for _, _, line in sorted(lines)))


def build_text_by_top_left(rows: list[dict]) -> str:
    if not rows:
        return ""
    ordered_rows = sorted(rows, key=lambda item: (item["top"], item["left"]))
    return normalize_ocr_text("\n".join(item["text"] for item in ordered_rows))


def build_vertical_text_from_ocr_words(rows: list[dict]) -> str:
    cjk_rows = [row for row in rows if chinese_char_count(row["text"]) > 0]
    if sum(chinese_char_count(row["text"]) for row in cjk_rows) < 4:
        return ""

    widths = sorted(row["width"] for row in cjk_rows if row["width"] > 0)
    median_width = widths[len(widths) // 2] if widths else 12
    column_tolerance = max(18, min(80, median_width * 2.5))

    columns: list[dict] = []
    for row in sorted(cjk_rows, key=ocr_row_center_x, reverse=True):
        center_x = ocr_row_center_x(row)
        matched_column = None
        for column in columns:
            if abs(center_x - column["center_x"]) <= column_tolerance:
                matched_column = column
                break
        if matched_column is None:
            columns.append({"center_x": center_x, "rows": [row]})
        else:
            matched_column["rows"].append(row)
            matched_column["center_x"] = sum(ocr_row_center_x(item) for item in matched_column["rows"]) / len(
                matched_column["rows"]
            )

    lines = []
    for column in sorted(columns, key=lambda item: item["center_x"], reverse=True):
        ordered_rows = sorted(column["rows"], key=lambda item: (item["top"], item["left"]))
        text = compact_chinese_text(join_ocr_tokens([item["text"] for item in ordered_rows]))
        if chinese_char_count(text) >= 2:
            lines.append(text)

    return normalize_ocr_text("\n".join(lines))


def ocr_row_center_x(row: dict) -> float:
    return row["left"] + row["width"] / 2


def clean_ocr_token(value: str) -> str:
    token = (value or "").strip()
    token = token.strip("|｜")
    token = re.sub(r"\s+", "", token)
    return token


def join_ocr_tokens(tokens: list[str]) -> str:
    text = ""
    for token in tokens:
        if not token:
            continue
        if not text:
            text = token
        elif should_join_ocr_tokens(text[-1], token[0]):
            text += token
        else:
            text += f" {token}"
    return text.strip()


def should_join_ocr_tokens(left_char: str, right_char: str) -> bool:
    if re.fullmatch(r"[\u4e00-\u9fff]", left_char) or re.fullmatch(r"[\u4e00-\u9fff]", right_char):
        return True
    return left_char.isdigit() and right_char.isdigit()


def parse_int(value: str | None, default: int = 0) -> int:
    try:
        return int(value or default)
    except (TypeError, ValueError):
        return default


def parse_float(value: str | None, default: float = 0) -> float:
    try:
        return float(value or default)
    except (TypeError, ValueError):
        return default


def dedupe_text_candidates(candidates: list[str]) -> list[str]:
    seen = set()
    deduped = []
    for candidate in candidates:
        normalized = normalize_ocr_text(candidate)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        deduped.append(normalized)
    return deduped


SPEAKER_LABELS = ("主讲人", "报告人", "嘉宾", "讲者", "主讲")
ORGANIZER_LABELS = ("主办方", "主办单位", "主办", "承办单位", "承办", "组织单位", "组织方")


def parse_single_candidate(text: str, default_year: int) -> dict:
    """Parse one OCR candidate text into raw (non-serialized) activity fields."""
    raw_text = normalize_ocr_text(text)
    lines = split_text_lines(raw_text)
    start_time, end_time = extract_time_range(raw_text, default_year)
    return {
        "text": raw_text,
        "lines": lines,
        "title": extract_title(lines),
        "location": extract_location(lines),
        "start_time": start_time,
        "end_time": end_time,
        "speaker": extract_labeled_value(lines, SPEAKER_LABELS),
        "organizer": extract_labeled_value(lines, ORGANIZER_LABELS),
    }


def parse_activity_from_candidates(candidates: list[str], default_year: int | None = None) -> dict:
    """Parse every OCR candidate independently, then pick the best value per field.

    This avoids the old "concatenate two texts and take the first match" approach,
    where a worse candidate placed first would win every field. Now each field is
    chosen on its own merit across all candidates, so a correct location coming from
    a different candidate than the title is still picked up.
    """
    default_year = default_year or datetime.now().year
    parsed = [parse_single_candidate(text, default_year) for text in candidates if text]

    title = pick_best((item["title"] for item in parsed), title_score)
    location = pick_best((item["location"] for item in parsed), location_score)
    start_time, end_time = pick_best_time(parsed)
    speaker = pick_first_value(item["speaker"] for item in parsed)
    organizer = pick_first_value(item["organizer"] for item in parsed)

    detail_text = max((item["text"] for item in parsed), key=ocr_detail_score, default="")
    full_text = normalize_ocr_text("\n".join(item["text"] for item in parsed))
    campus = infer_campus(location or full_text)
    category = infer_category(f"{title or ''}\n{full_text}")
    description = build_description(split_text_lines(detail_text), title)

    return {
        "title": title or "",
        "description": description,
        "speaker": speaker,
        "organizer": organizer,
        "college": None,
        "category": category,
        "campus": campus,
        "location": location,
        "start_time": start_time.isoformat() if start_time else None,
        "end_time": end_time.isoformat() if end_time else None,
        "source_url": None,
    }


def parse_activity_text(text: str, default_year: int | None = None) -> dict:
    """Parse a single text blob (kept for direct/single-text callers)."""
    return parse_activity_from_candidates([text], default_year)


def pick_best(values, scorer) -> str | None:
    """Return the non-empty value with the highest score, or None."""
    candidates = [value for value in values if value]
    if not candidates:
        return None
    best = max(candidates, key=scorer)
    return best if scorer(best) > -1000 else None


def pick_first_value(values) -> str | None:
    for value in values:
        if value:
            return value
    return None


def pick_best_time(parsed: list[dict]) -> tuple[datetime | None, datetime | None]:
    """Prefer a parse with both start and end time, then any with a start time."""
    with_range = [item for item in parsed if item["start_time"] and item["end_time"]]
    if with_range:
        best = with_range[0]
        return best["start_time"], best["end_time"]
    with_start = [item for item in parsed if item["start_time"]]
    if with_start:
        best = with_start[0]
        return best["start_time"], best["end_time"]
    return None, None


def location_score(value: str) -> float:
    """Score a location candidate, rewarding known campus names so OCR typos lose.

    e.g. "浙大紫金港校区..." beats "浙大昧金港校区..." because only the former
    contains a real campus name.
    """
    if not value:
        return -1000
    score = min(len(value), 30)
    if infer_campus(value):
        score += 30
    if looks_like_location(value):
        score += 8
    if chinese_char_count(value) < 2:
        score -= 30
    return score


def normalize_ocr_text(text: str) -> str:
    if not text:
        return ""
    replacements = {
        "\u3000": " ",
        "｜": "|",
        "：": ":",
        "（": "(",
        "）": ")",
        "，": ",",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)

    lines = []
    for line in text.splitlines():
        cleaned = re.sub(r"[ \t]+", " ", line).strip(" \t\r\n|")
        if cleaned:
            lines.append(cleaned)
    return "\n".join(lines)


def split_text_lines(text: str) -> list[str]:
    return [line.strip() for line in normalize_ocr_text(text).splitlines() if line.strip()]


def extract_title(lines: list[str]) -> str | None:
    title_labels = ("活动名称", "活动标题", "活动主题", "讲座题目", "报告题目", "讲座主题", "报告主题", "主题", "题目", "标题")
    for line in lines:
        value = extract_value_by_labels(line, title_labels)
        candidate = normalize_title_candidate(value or "")
        if candidate and is_possible_title(candidate):
            return candidate

    candidates = build_vertical_title_candidates(lines)
    candidates.extend(merge_colon_split_title_lines(lines))
    for line in lines:
        candidates.append(line)

    ranked_candidates = []
    for candidate in candidates:
        normalized = normalize_title_candidate(candidate)
        if normalized and is_possible_title(normalized):
            ranked_candidates.append(normalized)
    if not ranked_candidates:
        return None
    return max(ranked_candidates, key=title_score)


def merge_colon_split_title_lines(lines: list[str]) -> list[str]:
    """Join a title that OCR split across two visual lines at a trailing colon.

    A poster title like "法律制度中的国家与社会：/ 过去和当下的对话" is recognized
    as two lines, the first ending in a colon. On its own each half is a weaker
    title candidate; merged, it is the real, full title. We only merge when the
    next line looks like a continuation (not a labeled field such as 时间/地点),
    so "主题：" style label lines are left for the label-based path above.
    """
    merged = []
    non_title_label_words = ("时间", "日期", "地点", "地址", "场地", "教室", "主讲", "报告人", "嘉宾", "主办", "承办", "组织", "报名", "联系")
    for index, line in enumerate(lines[:-1]):
        if not re.search(r"[:：]\s*$", line):
            continue
        head = line.rstrip(" \t:：").strip()
        if not head or any(word in head for word in non_title_label_words):
            continue
        next_line = lines[index + 1].strip()
        if not is_possible_title(normalize_title_candidate(next_line)):
            continue
        if find_time_match(next_line) or find_date_match(next_line) or looks_like_location(next_line):
            continue
        merged.append(f"{head}：{next_line}")
    return merged



def extract_location(lines: list[str]) -> str | None:
    location_labels = ("会议地点", "活动地点", "举办地点", "地点", "地址", "场地", "教室")
    for line in lines:
        value = extract_value_by_labels(line, location_labels)
        if value:
            return clean_location(value)

    for line in lines:
        if looks_like_location(line):
            return clean_location(strip_date_time_parts(line))
    return None


def extract_labeled_value(lines: list[str], labels: tuple[str, ...]) -> str | None:
    for line in lines:
        value = extract_value_by_labels(line, labels)
        if value:
            return clean_field_value(value)
    return None


def extract_value_by_labels(line: str, labels: tuple[str, ...]) -> str | None:
    for label in labels:
        pattern = rf"(?:^|[\s,，;；]){re.escape(label)}\s*[:：]\s*(.+)$"
        match = re.search(pattern, line)
        if match:
            return match.group(1)
    return None


def extract_time_range(text: str, default_year: int) -> tuple[datetime | None, datetime | None]:
    date_match = find_date_match(text)
    time_match = find_time_match(text)
    if not date_match or not time_match:
        return None, None

    year = int(date_match.groupdict().get("year") or default_year)
    month = int(date_match.group("month"))
    day = int(date_match.group("day"))
    start_hour = int(time_match.group("start_hour"))
    start_minute = int(time_match.group("start_minute"))
    end_hour_value = time_match.groupdict().get("end_hour")
    end_minute_value = time_match.groupdict().get("end_minute")

    try:
        start_time = datetime(year, month, day, start_hour, start_minute)
    except ValueError:
        return None, None

    if not end_hour_value or not end_minute_value:
        return start_time, None

    try:
        end_time = datetime(year, month, day, int(end_hour_value), int(end_minute_value))
    except ValueError:
        return start_time, None

    if end_time < start_time:
        end_time += timedelta(days=1)
    return start_time, end_time


def find_date_match(text: str) -> re.Match[str] | None:
    patterns = [
        r"(?P<year>20\d{2})\s*[年./-]\s*(?P<month>1[0-2]|0?[1-9])\s*[月./-]\s*(?P<day>[12]\d|3[01]|0?[1-9])\s*(?:日|号)?",
        r"(?<!\d)(?P<month>1[0-2]|0?[1-9])\s*(?:月|/|\.)\s*(?P<day>[12]\d|3[01]|0?[1-9])\s*(?:日|号)?",
        r"(?<!\d)(?P<month>1[0-2]|0?[1-9])\s*-\s*(?P<day>[12]\d|3[01]|0?[1-9])(?!\d)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match
    return None


def find_time_match(text: str) -> re.Match[str] | None:
    pattern = (
        r"(?P<start_hour>[01]?\d|2[0-3])\s*[:：]\s*(?P<start_minute>[0-5]\d)"
        r"(?:\s*(?:-|--|—|–|~|～|至|到|一)\s*"
        r"(?P<end_hour>[01]?\d|2[0-3])\s*[:：]\s*(?P<end_minute>[0-5]\d))?"
    )
    return re.search(pattern, text)


def choose_display_text(results: list[str]) -> str:
    """Pick a single, most-informative candidate for the human-readable raw text.

    Field values are chosen separately in parse_activity_from_candidates, so this
    only needs to surface one clean block (no more double-pasted results).
    """
    candidates = dedupe_text_candidates(results)
    if not candidates:
        return ""
    return max(candidates, key=lambda text: ocr_text_score(text) + ocr_detail_score(text))


def choose_best_ocr_text(results: list[str]) -> str:
    candidates = dedupe_text_candidates(results)
    if not candidates:
        return ""
    best_title_text = max(candidates, key=ocr_text_score)
    best_detail_text = max(candidates, key=ocr_detail_score)
    return normalize_ocr_text(f"{best_title_text}\n{best_detail_text}")


def ocr_text_score(text: str) -> float:
    lines = split_text_lines(text)
    title = extract_title(lines)
    score = title_score(title or "") if title else 0
    score += min(len(normalize_ocr_text(text)), 200) / 200
    return score


def ocr_detail_score(text: str) -> float:
    normalized = normalize_ocr_text(text)
    score = min(len(normalized), 500) / 10
    if find_date_match(normalized):
        score += 20
    if find_time_match(normalized):
        score += 20
    if looks_like_location(normalized):
        score += 15
    if any(label in normalized for label in ("时间", "日期", "地点", "主讲", "嘉宾", "主办")):
        score += 10
    return score


def build_vertical_title_candidates(lines: list[str]) -> list[str]:
    candidates = []
    current_run: list[str] = []

    def flush_run():
        if sum(chinese_char_count(item) for item in current_run) >= 4:
            candidates.append("".join(current_run))
        current_run.clear()

    for line in lines:
        cleaned = normalize_title_candidate(line, strip_decorative=False)
        if is_vertical_fragment(cleaned):
            current_run.append(cleaned)
        else:
            flush_run()
            compact = compact_chinese_text(cleaned)
            if compact != cleaned and chinese_char_count(compact) >= 4:
                candidates.append(compact)
    flush_run()

    return candidates


def normalize_title_candidate(value: str, strip_decorative: bool = True) -> str:
    candidate = clean_field_value(value)
    if chinese_char_count(candidate) >= 2:
        candidate = compact_chinese_text(candidate)
    if strip_decorative:
        candidate = strip_decorative_title_words(candidate)
    return candidate.strip()


def strip_decorative_title_words(value: str) -> str:
    candidate = value.strip()
    for word in DECORATIVE_TITLE_WORDS:
        if candidate == word:
            return ""
        if candidate.startswith(word) and chinese_char_count(candidate[len(word) :]) >= 4:
            candidate = candidate[len(word) :]
        if candidate.endswith(word) and chinese_char_count(candidate[: -len(word)]) >= 4:
            candidate = candidate[: -len(word)]
    return candidate.strip()


def title_score(candidate: str) -> float:
    if not candidate:
        return -1000
    score = min(len(candidate), 30)
    if chinese_char_count(candidate) >= 4:
        score += 6
    if any(keyword in candidate for keyword in ACTIVITY_TITLE_KEYWORDS):
        score += 20
    if candidate in DECORATIVE_TITLE_WORDS:
        score -= 100
    if len(candidate) > 32:
        score -= (len(candidate) - 32) * 3
    if len(candidate) <= 3:
        score -= 8
    return score


def is_vertical_fragment(line: str) -> bool:
    return bool(re.fullmatch(r"[\u4e00-\u9fff]{1,2}", line or ""))


def compact_chinese_text(value: str) -> str:
    if not value:
        return ""
    if chinese_char_count(value) == 0:
        return re.sub(r"\s+", " ", value).strip()
    return re.sub(r"[\s|｜]+", "", value)


def chinese_char_count(value: str) -> int:
    return len(re.findall(r"[\u4e00-\u9fff]", value or ""))


def is_possible_title(line: str) -> bool:
    if not line or len(line) < 2 or len(line) > 60:
        return False
    if line in DECORATIVE_TITLE_WORDS:
        return False
    lower = line.lower()
    skip_keywords = (
        "时间",
        "日期",
        "地点",
        "地址",
        "主讲",
        "报告人",
        "嘉宾",
        "主办",
        "承办",
        "组织",
        "报名",
        "联系人",
        "联系电话",
        "会议号",
        "腾讯会议",
        "zoom",
        "http",
        "www.",
        "扫码",
        "二维码",
        "欢迎参加",
    )
    if any(keyword in lower for keyword in skip_keywords):
        return False
    if find_time_match(line) or find_date_match(line):
        return False
    if looks_like_location(line):
        return False
    return True


def looks_like_location(line: str) -> bool:
    location_keywords = (
        "紫金港",
        "玉泉",
        "西溪",
        "华家池",
        "之江",
        "海宁",
        "校区",
        "教学楼",
        "教室",
        "报告厅",
        "会议室",
        "实验室",
        "图书馆",
        "楼",
        "厅",
        "馆",
        "室",
    )
    return any(keyword in line for keyword in location_keywords)


def strip_date_time_parts(line: str) -> str:
    cleaned = re.sub(
        r"20\d{2}\s*[年./-]\s*\d{1,2}\s*[月./-]\s*\d{1,2}\s*(?:日|号)?",
        "",
        line,
    )
    cleaned = re.sub(r"(?<!\d)\d{1,2}\s*(?:月|/|-|\.)\s*\d{1,2}\s*(?:日|号)?", "", cleaned)
    cleaned = re.sub(
        r"\d{1,2}\s*[:：]\s*\d{2}(?:\s*(?:-|--|—|–|~|～|至|到)\s*\d{1,2}\s*[:：]\s*\d{2})?",
        "",
        cleaned,
    )
    return cleaned


def clean_location(value: str) -> str:
    cleaned = clean_field_value(value)
    cleaned = strip_date_time_parts(cleaned)
    cleaned = re.sub(r"^[\s,，;；·.。/-]+", "", cleaned)
    return cleaned or clean_field_value(value)


def clean_field_value(value: str) -> str:
    value = re.sub(r"^[\-—–~·•*#\s]+", "", value or "")
    value = re.split(
        r"\s+(?:时间|日期|地点|地址|主讲人|报告人|嘉宾|主办方|主办|承办|组织单位)\s*[:：]",
        value,
        maxsplit=1,
    )[0]
    return value.strip(" \t\r\n,，;；.。:：")


def infer_campus(text: str) -> str | None:
    for campus in ("紫金港", "玉泉", "西溪", "华家池", "之江", "海宁"):
        if campus in text:
            return campus
    return None


def infer_category(text: str) -> str | None:
    if any(keyword in text for keyword in ("工作坊", "Workshop", "workshop", "实训", "训练营")):
        return "工作坊"
    if any(keyword in text for keyword in ("研讨", "论坛", "会议", "Seminar", "seminar")):
        return "研讨会"
    if any(keyword in text for keyword in ("讲座", "报告", "学术", "Lecture", "lecture", "Talk", "talk")):
        return "学术讲座"
    return None


def build_description(lines: list[str], title: str | None) -> str | None:
    description_lines = []
    seen = set()
    for line in lines:
        if title and line == title:
            continue
        if line in seen:
            continue
        seen.add(line)
        description_lines.append(line)
    description = "\n".join(description_lines).strip()
    return description[:1000] if description else None


def build_parse_warnings(activity: dict) -> list[str]:
    warnings = []
    if not activity.get("title"):
        warnings.append("未识别到活动标题")
    if not activity.get("start_time"):
        warnings.append("未识别到完整活动时间")
    elif not activity.get("end_time"):
        warnings.append("未识别到结束时间，请填写预计时长")
    if not activity.get("location"):
        warnings.append("未识别到活动地点")
    return warnings
