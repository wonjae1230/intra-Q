"""질문에서 입학년도(학번)를 추출하고 검색 대상 교과과정 연도를 반환."""

from __future__ import annotations

import re

_DEFAULT_CURRICULUM_YEAR = 2025

# 입학년도 → 적용 교과과정 연도 목록 (DB 연동 전 하드코딩)
# 향후 CurriculumYearMapping 테이블로 대체 예정
_ADMISSION_TO_CURRICULUM: dict[int, list[int]] = {
    2021: [2021],
    2022: [2022],
    2023: [2022, 2023],
    2024: [2023, 2024],
    2025: [2024, 2025],
}


def extract_admission_year(question: str) -> int | None:
    """질문에서 학번/입학년도 추출.

    지원 패턴:
      "23학번", "2023학번", "23 학번", "2023 학번"
    """
    patterns = [
        r"(20\d{2})\s*학번",
        r"\b(\d{2})\s*학번",
    ]
    for pattern in patterns:
        m = re.search(pattern, question)
        if m:
            year = int(m.group(1))
            return year + 2000 if year < 100 else year
    return None


def get_curriculum_years(question: str) -> list[int]:
    """질문에서 적용 가능한 교과과정 연도 목록 반환.

    학번이 있으면 매핑 테이블 기준 연도 반환.
    학번이 없으면 최신 기본 연도 반환.
    """
    admission_year = extract_admission_year(question)
    if admission_year is None:
        return [_DEFAULT_CURRICULUM_YEAR]
    return _ADMISSION_TO_CURRICULUM.get(admission_year, [admission_year])
