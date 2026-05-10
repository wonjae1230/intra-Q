from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.session import Base
from app.models.chat_message import ChatMessage
from app.models.user import User
from app.services.chat_history_service import list_recent_chat_history


def test_list_recent_chat_history_limits_latest_rows_and_returns_ascending_order() -> None:
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()
    try:
        user = User(email="recent@example.com", nickname="Recent User", password_hash="hashed")
        other_user = User(email="other@example.com", nickname="Other User", password_hash="hashed")
        db.add_all([user, other_user])
        db.flush()

        base_time = datetime(2026, 5, 10, 12, 30, 0)
        messages = [
            ChatMessage(
                user_id=user.id,
                role="user",
                content=f"user message {index}",
                content_length=len(f"user message {index}"),
                created_at=base_time + timedelta(seconds=index),
            )
            for index in range(4)
        ]
        messages.append(
            ChatMessage(
                user_id=other_user.id,
                role="assistant",
                content="other user message",
                content_length=len("other user message"),
                created_at=base_time + timedelta(seconds=10),
            )
        )
        db.add_all(messages)
        db.commit()

        recent = list_recent_chat_history(db, user_id=user.id, limit=2)

        assert [message.content for message in recent] == ["user message 2", "user message 3"]
        assert [message.created_at for message in recent] == sorted(message.created_at for message in recent)
    finally:
        db.close()
