from __future__ import annotations

import re
from typing import Any


ALLOWED_CATEGORIES = {"전공필수", "전공선택", "교양필수", "교양선택", "계열선택", "심화"}
ALLOWED_SEMESTERS = {"1학기", "2학기", "매학기"}


def validate_subject(data: dict[str, Any]) -> dict[str, Any]:
    """Validate one normalized curriculum subject payload with deterministic rules."""
    errors: list[str] = []

    subject_code = str(data.get("subject_code") or "").strip()
    if not re.fullmatch(r"\d{6}", subject_code):
        errors.append("subject_code must be exactly 6 digits")

    credit = data.get("credit")
    try:
        credit_value = int(credit)
    except (TypeError, ValueError):
        errors.append("credit must be an integer between 1 and 6")
    else:
        if not 1 <= credit_value <= 6:
            errors.append("credit must be between 1 and 6")

    category = str(data.get("category") or "").strip()
    if category not in ALLOWED_CATEGORIES:
        errors.append(f"category must be one of: {', '.join(sorted(ALLOWED_CATEGORIES))}")

    semester = str(data.get("semester") or "").strip()
    if semester not in ALLOWED_SEMESTERS:
        errors.append(f"semester must be one of: {', '.join(sorted(ALLOWED_SEMESTERS))}")

    return {"valid": not errors, "errors": errors}
