from sqlalchemy import inspect, text

from app.db.session import Base, engine
from app.models.chat_message import ChatMessage
from app.models.chat_session import ChatSession
from app.models.chunk import Chunk
from app.models.document import Document
from app.models.user import User


def _add_column_if_missing(table_name: str, column_name: str, ddl: str) -> None:
    """Apply a tiny SQLite-compatible schema patch for existing local DB files."""
    inspector = inspect(engine)
    existing_columns = {column["name"] for column in inspector.get_columns(table_name)}
    if column_name in existing_columns:
        return

    with engine.begin() as connection:
        connection.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {ddl}"))


def _backfill_chat_sessions_for_existing_messages() -> None:
    """Group old single-history messages into one session per user when reusing SQLite DBs."""
    with engine.begin() as connection:
        rows = connection.execute(
            text(
                """
                SELECT DISTINCT user_id
                FROM chat_messages
                WHERE user_id IS NOT NULL
                  AND session_id IS NULL
                """
            )
        ).fetchall()

        for row in rows:
            user_id = row[0]
            first_message = connection.execute(
                text(
                    """
                    SELECT content
                    FROM chat_messages
                    WHERE user_id = :user_id
                      AND session_id IS NULL
                    ORDER BY created_at ASC, id ASC
                    LIMIT 1
                    """
                ),
                {"user_id": user_id},
            ).scalar()
            title = str(first_message or "이전 대화").strip()[:100] or "이전 대화"

            connection.execute(
                text(
                    """
                    INSERT INTO chat_sessions (user_id, title, created_at, updated_at)
                    VALUES (:user_id, :title, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    """
                ),
                {"user_id": user_id, "title": title},
            )
            session_id = connection.execute(text("SELECT last_insert_rowid()")).scalar_one()
            connection.execute(
                text(
                    """
                    UPDATE chat_messages
                    SET session_id = :session_id
                    WHERE user_id = :user_id
                      AND session_id IS NULL
                    """
                ),
                {"session_id": session_id, "user_id": user_id},
            )


def init_db() -> None:
    """Create all database tables if they do not already exist."""
    # Importing models above registers them with SQLAlchemy metadata.
    Base.metadata.create_all(bind=engine)

    # SQLAlchemy create_all does not alter existing SQLite tables, so add MVP auth
    # ownership columns when an older local database is reused.
    _add_column_if_missing("documents", "user_id", "user_id INTEGER REFERENCES users(id)")
    _add_column_if_missing("chat_messages", "user_id", "user_id INTEGER REFERENCES users(id)")
    _add_column_if_missing("chat_messages", "session_id", "session_id INTEGER REFERENCES chat_sessions(id)")
    _backfill_chat_sessions_for_existing_messages()
