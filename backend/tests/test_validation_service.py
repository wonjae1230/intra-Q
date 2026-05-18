from app.services.validation_service import validate_subject


def test_validate_subject_accepts_valid_curriculum_subject() -> None:
    result = validate_subject(
        {
            "subject_code": "123456",
            "credit": 3,
            "category": "전공필수",
            "semester": "1학기",
        }
    )

    assert result == {"valid": True, "errors": []}


def test_validate_subject_reports_rule_errors() -> None:
    result = validate_subject(
        {
            "subject_code": "ABC123",
            "credit": 7,
            "category": "기타",
            "semester": "여름",
        }
    )

    assert result["valid"] is False
    assert len(result["errors"]) == 4
