"""학번/연도 추출 로직 단위 테스트."""

from __future__ import annotations

import pytest

from rag.curriculum.year_extractor import extract_admission_year, get_curriculum_years


@pytest.mark.parametrize(
    "question, expected",
    [
        ("23학번인데 인공지능 들어야 해?", 2023),
        ("2023학번 교과과정 알려줘", 2023),
        ("21학번 졸업요건 뭐야", 2021),
        ("2021 학번 커리큘럼", 2021),
        ("24 학번인데 전공 몇 학점?", 2024),
        ("학번 없는 질문", None),
        ("인공지능 수업 있나요?", None),
    ],
)
def test_extract_admission_year(question: str, expected: int | None) -> None:
    assert extract_admission_year(question) == expected


@pytest.mark.parametrize(
    "question, expected_years",
    [
        ("23학번 인공지능 과목", [2022, 2023]),
        ("21학번 졸업요건", [2021]),
        ("학번 없는 일반 질문", [2025]),
    ],
)
def test_get_curriculum_years(question: str, expected_years: list[int]) -> None:
    assert get_curriculum_years(question) == expected_years
