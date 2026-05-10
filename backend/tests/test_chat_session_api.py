from __future__ import annotations

from fastapi.testclient import TestClient

from app.database.session import SessionLocal
from app.main import app
from app.services.chat_history_service import save_user_message


def test_get_session_messages_returns_saved_messages_without_response_validation_error() -> None:
    client = TestClient(app)
    email = "session-api@example.com"
    password = "Password123!"

    client.post("/api/auth/register", json={"email": email, "password": password, "nickname": "Session API"})
    login_response = client.post("/api/auth/login", json={"email": email, "password": password})
    token = login_response.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    session_response = client.post("/api/chat/sessions", headers=headers, json={"title": "API test"})
    session_id = session_response.json()["data"]["session_id"]
    user_id = client.get("/api/auth/me", headers=headers).json()["data"]["id"]

    db = SessionLocal()
    try:
        save_user_message(db, user_id=user_id, session_id=session_id, content="세션 메시지")
    finally:
        db.close()

    messages_response = client.get(
        f"/api/chat/sessions/{session_id}/messages?limit=50&offset=0&order=asc",
        headers=headers,
    )

    assert messages_response.status_code == 200
    payload = messages_response.json()
    assert payload["success"] is True
    assert payload["data"][0]["session_id"] == session_id
    assert payload["data"][0]["content"] == "세션 메시지"
