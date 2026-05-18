from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from fastapi.testclient import TestClient

from app.database.session import SessionLocal
from app.main import app
from app.models.curriculum_mapping import CurriculumMapping
from app.models.document import Document
from app.models.page_log import PageLog
from app.models.subject import Subject


def test_admin_page_log_filters_failed_pages_retry_and_mapping_patch() -> None:
    client = TestClient(app)
    headers = _auth_headers(client)
    db = SessionLocal()
    try:
        document = Document(
            file_name="admin-test.pdf",
            page_count=2,
            curriculum_year=2024,
            department="컴퓨터공학과",
            source_file="admin-test.pdf",
            processing_status="completed",
        )
        db.add(document)
        db.flush()
        failed_log = PageLog(
            document_id=document.id,
            page_id=f"test_{uuid4().hex[:8]}_p1",
            page_number=1,
            page_type="D",
            process_method="pymupdf",
            validation_status="failed",
            failure_reason="mock failure",
            processed_at=datetime.utcnow(),
        )
        passed_log = PageLog(
            document_id=document.id,
            page_id=f"test_{uuid4().hex[:8]}_p2",
            page_number=2,
            page_type="C",
            process_method="pymupdf",
            validation_status="passed",
            processed_at=datetime.utcnow(),
        )
        mapping = CurriculumMapping(
            admission_year=2023,
            department="컴퓨터공학과",
            curriculum_years=[2023],
        )
        db.add_all([failed_log, passed_log, mapping])
        db.commit()
        db.refresh(document)
        db.refresh(failed_log)
        db.refresh(mapping)

        page_logs_response = client.get(
            f"/api/admin/page-logs?document_id={document.id}&validation_status=failed",
            headers=headers,
        )
        assert page_logs_response.status_code == 200
        page_log_data = page_logs_response.json()["data"]
        assert len(page_log_data) == 1
        assert page_log_data[0]["page_id"] == failed_log.page_id

        failed_pages_response = client.get(f"/api/admin/failed-pages?document_id={document.id}", headers=headers)
        assert failed_pages_response.status_code == 200
        assert [row["page_id"] for row in failed_pages_response.json()["data"]] == [failed_log.page_id]

        retry_response = client.post(f"/api/admin/pages/{failed_log.page_id}/retry", headers=headers)
        assert retry_response.status_code == 200
        assert retry_response.json()["data"]["validation_status"] == "passed"

        mapping_list_response = client.get(
            "/api/admin/curriculum-mappings?department=컴퓨터공학과&admission_year=23",
            headers=headers,
        )
        assert mapping_list_response.status_code == 200
        assert mapping_list_response.json()["data"]

        patch_response = client.patch(
            f"/api/admin/curriculum-mappings/{mapping.id}",
            headers=headers,
            json={"curriculum_years": [2022, 2023], "department": "컴퓨터공학과"},
        )
        assert patch_response.status_code == 200
        assert patch_response.json()["data"]["curriculum_years"] == [2022, 2023]
    finally:
        if "document" in locals():
            db.query(Subject).filter(Subject.document_id == document.id).delete(synchronize_session=False)
            db.query(PageLog).filter(PageLog.document_id == document.id).delete(synchronize_session=False)
            db.query(Document).filter(Document.id == document.id).delete(synchronize_session=False)
        if "mapping" in locals():
            db.query(CurriculumMapping).filter(CurriculumMapping.id == mapping.id).delete(synchronize_session=False)
        db.commit()
        db.close()


def _auth_headers(client: TestClient) -> dict[str, str]:
    email = f"admin-api-{uuid4().hex[:8]}@example.com"
    password = "Password123!"
    client.post("/api/auth/register", json={"email": email, "password": password, "nickname": "Admin API"})
    login = client.post("/api/auth/login", json={"email": email, "password": password})
    assert login.status_code == 200
    return {"Authorization": f"Bearer {login.json()['data']['access_token']}"}
