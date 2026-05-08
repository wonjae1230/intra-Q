from sqlalchemy import inspect, text

from app.db.session import Base, engine
from app.models.chat_message import ChatMessage
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


def init_db() -> None:
    """Create all database tables if they do not already exist."""
    # Importing models above registers them with SQLAlchemy metadata.
    Base.metadata.create_all(bind=engine)

    # SQLAlchemy create_all does not alter existing SQLite tables, so add MVP auth
    # ownership columns when an older local database is reused.
    _add_column_if_missing("documents", "user_id", "user_id INTEGER REFERENCES users(id)")
    _add_column_if_missing("chat_messages", "user_id", "user_id INTEGER REFERENCES users(id)")
