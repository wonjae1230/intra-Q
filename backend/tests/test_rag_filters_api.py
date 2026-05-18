from __future__ import annotations

from uuid import uuid4

from fastapi.testclient import TestClient

from app.database.session import SessionLocal
from app.main import app
from app.models.curriculum_mapping import CurriculumMapping


def test_rag_filter_resolve_uses_question_admission_year_and_mapping() -> None:
    client = TestClient(app)
    headers = _auth_headers(client)
    db = SessionLocal()
    try:
        mapping = CurriculumMapping(
            admission_year=2023,
            department="소프트웨어융합",
            curriculum_years=[2022, 2023],
        )
        db.add(mapping)
        db.commit()
        db.refresh(mapping)

        response = client.post(
            "/api/rag/filters/resolve",
            headers=headers,
            json={
                "question": "23학번인데 인공지능 들어야 하나요?",
                "department": "소프트웨어융합",
                "admission_year": None,
            },
        )

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["admission_year"] == 2023
        assert data["curriculum_years"] == [2022, 2023]
        assert data["fallback_used"] is False
    finally:
        if "mapping" in locals():
            db.query(CurriculumMapping).filter(CurriculumMapping.id == mapping.id).delete(synchronize_session=False)
            db.commit()
        db.close()


def _auth_headers(client: TestClient) -> dict[str, str]:
    email = f"rag-filter-{uuid4().hex[:8]}@example.com"
    password = "Password123!"
    client.post("/api/auth/register", json={"email": email, "password": password, "nickname": "RAG Filter"})
    login = client.post("/api/auth/login", json={"email": email, "password": password})
    assert login.status_code == 200
    return {"Authorization": f"Bearer {login.json()['data']['access_token']}"}
