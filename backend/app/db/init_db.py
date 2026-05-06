from app.db.session import Base, engine
from app.models.chunk import Chunk
from app.models.document import Document


def init_db() -> None:
    """Create all database tables if they do not already exist."""
    # Importing models above registers them with SQLAlchemy metadata.
    Base.metadata.create_all(bind=engine)
