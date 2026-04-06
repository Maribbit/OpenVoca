from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, create_engine


def _in_memory_engine():
    """Create a fresh in-memory SQLite engine for test isolation."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )
    SQLModel.metadata.create_all(engine)
    return engine
