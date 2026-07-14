"""
Database Connection & Session Management
=========================================

Manages the SQLAlchemy engine, session factory, and provides a dependency-
injectable ``get_db_session()`` generator for FastAPI.

Architecture:
    - Uses SQLAlchemy 2.0 style with ``create_engine`` and ``sessionmaker``.
    - The ``init_db()`` function creates all tables on first run.
    - ``get_db_session()`` is a generator that yields a session and
      ensures cleanup via try/finally (used with FastAPI ``Depends``).

Usage::

    from src.db.database import get_db_session, init_db

    # At application startup:
    init_db()

    # In FastAPI routes (via Depends):
    @app.get("/items")
    def list_items(db: Session = Depends(get_db_session)):
        ...
"""

from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.core.config import get_settings

# ---------------------------------------------------------------------------
# Engine & Session Factory
# ---------------------------------------------------------------------------

_settings = get_settings()

# Ensure the data directory exists for SQLite
_db_path = _settings.database_url.replace("sqlite:///", "")
if _db_path:
    Path(_db_path).parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(
    _settings.database_url,
    echo=_settings.debug,
    connect_args={"check_same_thread": False},  # Required for SQLite + threads
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


# ---------------------------------------------------------------------------
# Session Dependency
# ---------------------------------------------------------------------------


def get_db_session() -> Generator[Session, None, None]:
    """
    Yield a database session and ensure cleanup.

    This is designed to be used as a FastAPI dependency via ``Depends(get_db_session)``.
    The session is automatically closed after the request completes, even if
    an exception occurs.

    Yields:
        SQLAlchemy Session instance.
    """
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


# ---------------------------------------------------------------------------
# Database Initialization
# ---------------------------------------------------------------------------


def init_db() -> None:
    """
    Create all database tables defined in ``src.db.models``.

    Safe to call multiple times — SQLAlchemy's ``create_all`` only creates
    tables that don't already exist.

    This function should be called once during application startup
    (in the FastAPI lifespan handler or ``main.py``).
    """
    from src.db.models import Base  # Local import to avoid circular dependency

    Base.metadata.create_all(bind=engine)
