import pytest

from app.services import activity_ocr_service
from app.services.activity_ocr_service import parse_activity_text, recognize_activity_images


def test_parse_activity_text_with_chinese_labels():
    text = """
    人工智能前沿讲座
    时间：2026年5月10日 14:00-16:00
    地点：紫金港东1A-101
    主讲人：张三教授
    主办单位：计算机科学与技术学院
    """

    activity = parse_activity_text(text)

    assert activity["title"] == "人工智能前沿讲座"
    assert activity["speaker"] == "张三教授"
    assert activity["organizer"] == "计算机科学与技术学院"
    assert activity["campus"] == "紫金港"
    assert activity["location"] == "紫金港东1A-101"
    assert activity["category"] == "学术讲座"
    assert activity["start_time"] == "2026-05-10T14:00:00"
    assert activity["end_time"] == "2026-05-10T16:00:00"


def test_parse_activity_text_with_split_date_and_time():
    text = """
    活动名称：青年学者研讨会
    日期：5月11日
    时间：09:30 至 11:00
    活动地点：玉泉校区永谦活动中心
    """

    activity = parse_activity_text(text, default_year=2026)

    assert activity["title"] == "青年学者研讨会"
    assert activity["category"] == "研讨会"
    assert activity["campus"] == "玉泉"
    assert activity["location"] == "玉泉校区永谦活动中心"
    assert activity["start_time"] == "2026-05-11T09:30:00"
    assert activity["end_time"] == "2026-05-11T11:00:00"


def test_parse_activity_text_with_activity_theme_time_and_location_labels():
    text = """
    活动主题：求是创新--浙大医学在义乌的发展实践
    活动时间：6月2日（周二）11:40-13:30
    活动地点：东一A102会议室
    """

    activity = parse_activity_text(text, default_year=2026)

    assert activity["title"] == "求是创新--浙大医学在义乌的发展实践"
    assert activity["location"] == "东一A102会议室"
    assert activity["start_time"] == "2026-06-02T11:40:00"
    assert activity["end_time"] == "2026-06-02T13:30:00"


def test_parse_activity_text_extracts_location_from_compact_line():
    text = """
    机器学习课程
    5-10 · 紫金港东1A-101
    13:00-15:00
    """

    activity = parse_activity_text(text, default_year=2026)

    assert activity["title"] == "机器学习课程"
    assert activity["campus"] == "紫金港"
    assert activity["location"] == "紫金港东1A-101"
    assert activity["start_time"] == "2026-05-10T13:00:00"
    assert activity["end_time"] == "2026-05-10T15:00:00"


def test_parse_activity_text_keeps_missing_end_time_empty():
    text = """
    校园十佳歌手大赛决赛
    时间：2026年5月25日 19:00
    地点：紫金港小剧场
    """

    activity = parse_activity_text(text)

    assert activity["title"] == "校园十佳歌手大赛决赛"
    assert activity["start_time"] == "2026-05-25T19:00:00"
    assert activity["end_time"] is None
    assert "未识别到结束时间，请填写预计时长" in activity_ocr_service.build_parse_warnings(activity)


def test_parse_activity_text_merges_colon_split_title_across_two_lines():
    text = """
    法律制度中的国家与社会：
    过去和当下的对话
    时间：2026年6月7日（周日）13:30
    地点：浙江大学紫金港校区成均苑8幢1127
    """

    activity = parse_activity_text(text)

    assert activity["title"] == "法律制度中的国家与社会：过去和当下的对话"
    assert activity["campus"] == "紫金港"
    assert activity["start_time"] == "2026-06-07T13:30:00"


def test_parse_activity_text_skips_poster_decorative_title():
    text = """
    节目单
    校园十佳歌手大赛决赛
    """

    activity = parse_activity_text(text)

    assert activity["title"] == "校园十佳歌手大赛决赛"


def test_parse_activity_text_rebuilds_vertical_title_characters():
    text = """
    节
    目
    单
    校
    园
    十
    佳
    歌
    手
    大
    赛
    决
    赛
    """

    activity = parse_activity_text(text)

    assert activity["title"] == "校园十佳歌手大赛决赛"


def test_extract_text_candidates_from_tsv_rebuilds_vertical_columns():
    columns = [
        "level",
        "page_num",
        "block_num",
        "par_num",
        "line_num",
        "word_num",
        "left",
        "top",
        "width",
        "height",
        "conf",
        "text",
    ]
    rows = []

    def add_row(text, left, top, word_num):
        rows.append(
            [
                "5",
                "1",
                "1",
                "1",
                "1",
                str(word_num),
                str(left),
                str(top),
                "24",
                "32",
                "88",
                text,
            ]
        )

    for index, char in enumerate("校园十佳歌手大赛决赛", start=1):
        add_row(char, 520, 20 + index * 34, index)
    for index, char in enumerate("节目单", start=20):
        add_row(char, 250, 20 + (index - 19) * 58, index)

    tsv_text = "\n".join(["\t".join(columns), *("\t".join(row) for row in rows)])

    candidates = activity_ocr_service.extract_text_candidates_from_tsv(tsv_text)
    activity = parse_activity_text("\n".join(candidates))

    assert any("校园十佳歌手大赛决赛" in candidate for candidate in candidates)
    assert activity["title"] == "校园十佳歌手大赛决赛"


def test_choose_best_ocr_text_keeps_title_and_detail_candidates():
    title_crop_text = "校园十佳歌手大赛决赛"
    full_image_text = """
    时间：2026年5月25日 19:00-21:00
    地点：紫金港小剧场
    """

    merged_text = activity_ocr_service.choose_best_ocr_text([full_image_text, title_crop_text])
    activity = parse_activity_text(merged_text)

    assert activity["title"] == "校园十佳歌手大赛决赛"
    assert activity["location"] == "紫金港小剧场"
    assert activity["start_time"] == "2026-05-25T19:00:00"
    assert activity["end_time"] == "2026-05-25T21:00:00"


def test_build_ocr_image_variants_uses_original_when_imagemagick_missing(monkeypatch):
    monkeypatch.setattr(activity_ocr_service, "find_imagemagick_command", lambda: None)
    monkeypatch.setattr(activity_ocr_service, "is_tesseract_language_available", lambda _: False)

    variants = activity_ocr_service.build_ocr_image_variants("/tmp/source.png", "/tmp")

    assert variants == [("/tmp/source.png", "original")]


def test_recognize_activity_images_merges_up_to_five_screenshots(monkeypatch):
    texts = [
        "人工智能前沿讲座\n时间：2026年5月10日 14:00-16:00",
        "地点：紫金港东1A-101\n主讲人：张三教授",
    ]

    def fake_run_tesseract_image(filename, content):
        return texts.pop(0)

    monkeypatch.setattr(activity_ocr_service, "run_tesseract_image", fake_run_tesseract_image)

    result = recognize_activity_images(
        [
            ("one.png", b"first"),
            ("two.png", b"second"),
        ]
    )

    assert result["filenames"] == ["one.png", "two.png"]
    assert len(result["screenshots"]) == 2
    assert result["activity"]["title"] == "人工智能前沿讲座"
    assert result["activity"]["location"] == "紫金港东1A-101"
    assert result["activity"]["speaker"] == "张三教授"


def test_recognize_activity_images_rejects_more_than_five_screenshots():
    files = [(f"{index}.png", b"image") for index in range(6)]

    with pytest.raises(ValueError, match="最多支持 5 张截图"):
        recognize_activity_images(files)
