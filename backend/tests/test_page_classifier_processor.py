from app.services.page_classifier import classify_page
from app.services.page_processor import process_page


def test_classify_page_returns_type_a_for_image_heavy_page() -> None:
    result = classify_page("", {"page_number": 1, "image_count": 2, "text_length": 0})

    assert result["page_type"] == "A"


def test_classify_page_returns_type_c_for_table_like_text() -> None:
    text = "\n".join(
        [
            "교과목 번호  과목명  학점",
            "123456  인공지능  3",
            "전공선택  1학기",
        ]
    )

    result = classify_page(text, {"page_number": 2})

    assert result["page_type"] == "C"


def test_process_page_type_a_marks_gemini_required_without_calling_gemini() -> None:
    result = process_page("A", {"page": 1, "text": ""})

    assert result["method"] == "gemini"
    assert result["requires_gemini"] is True
    assert result["failure_reason"]
