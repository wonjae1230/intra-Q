from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.session import Base
from app.models.curriculum_mapping import CurriculumMapping
from app.models.document import Document
from app.services.curriculum_service import extract_admission_year, resolve_curriculum_years


def test_extract_admission_year_normalizes_two_digit_year() -> None:
    assert extract_admission_year("23학번인데 인공지능 들어야 하나요?") == 2023


def test_resolve_curriculum_years_returns_mapping() -> None:
    db = _memory_session()
    try:
        db.add(
            CurriculumMapping(
                admission_year=2023,
                department="소프트웨어융합",
                curriculum_years=[2022, 2023],
            )
        )
        db.commit()

        assert resolve_curriculum_years(db, admission_year=23, department="소프트웨어융합") == [2022, 2023]
    finally:
        db.close()


def test_resolve_curriculum_years_falls_back_to_latest_document_year() -> None:
    db = _memory_session()
    try:
        db.add(
            Document(
                file_name="curriculum.pdf",
                page_count=1,
                curriculum_year=2024,
                department="컴퓨터공학과",
            )
        )
        db.commit()

        assert resolve_curriculum_years(db, admission_year=2021, department="컴퓨터공학과") == [2024]
    finally:
        db.close()


def _memory_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    testing_session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return testing_session_local()
