from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.session import Base
from app.models.chat_message import ChatMessage
from app.models.chat_session import ChatSession
from app.models.user import User
from app.services.chat_history_service import list_session_messages
from app.services.chat_session_service import (
    create_chat_session,
    delete_chat_session,
    get_owned_chat_session,
    list_chat_sessions,
)


def test_chat_sessions_are_user_scoped_and_delete_owned_messages() -> None:
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()
    try:
        user = User(email="owner@example.com", nickname="Owner", password_hash="hashed")
        other_user = User(email="other-owner@example.com", nickname="Other", password_hash="hashed")
        db.add_all([user, other_user])
        db.flush()

        created = create_chat_session(db, user_id=user.id, title="연차 정책 질문")
        session = db.query(ChatSession).filter(ChatSession.id == created.session_id).one()
        other_session = ChatSession(user_id=other_user.id, title="다른 사용자 세션")
        db.add(other_session)
        db.flush()

        db.add_all(
            [
                ChatMessage(
                    user_id=user.id,
                    session_id=session.id,
                    role="user",
                    content="연차 정책 알려줘",
                    content_length=len("연차 정책 알려줘"),
                ),
                ChatMessage(
                    user_id=other_user.id,
                    session_id=other_session.id,
                    role="user",
                    content="다른 사용자 메시지",
                    content_length=len("다른 사용자 메시지"),
                ),
            ]
        )
        db.commit()

        messages = list_session_messages(db, user_id=user.id, session_id=session.id)
        sessions = list_chat_sessions(db, user_id=user.id)

        assert [message.content for message in messages] == ["연차 정책 알려줘"]
        assert sessions[0].message_count == 1
        assert sessions[0].last_message == "연차 정책 알려줘"

        try:
            get_owned_chat_session(db, user_id=user.id, session_id=other_session.id)
        except Exception as exc:
            assert getattr(exc, "status_code", None) == 403
        else:
            raise AssertionError("Cross-user session access should be forbidden")

        deleted = delete_chat_session(db, user_id=user.id, session_id=session.id)

        assert deleted.deleted_messages == 1
        assert list_session_messages(db, user_id=user.id, session_id=session.id) == []
    finally:
        db.close()
