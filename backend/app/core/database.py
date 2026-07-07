"""
SQLAlchemy database engine, session factory, and dependency injection.

Uses synchronous psycopg (v3) driver. The Repository abstraction layer
makes a future migration to async (asyncpg) straightforward without
changing the service or API layers.

The engine and session factory are created lazily to avoid connection
attempts at import time (useful for testing and CLI tools).
"""

from collections.abc import Generator
from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config.settings import get_settings


class Base(DeclarativeBase):
    """Declarative base shared by all SQLAlchemy models."""


@lru_cache
def get_engine():
    """Create and cache the SQLAlchemy engine."""
    settings = get_settings()
    return create_engine(
        settings.DATABASE_URL,
        echo=settings.DEBUG,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,
    )


@lru_cache
def get_session_factory() -> sessionmaker[Session]:
    """Create and cache the session factory."""
    return sessionmaker(
        bind=get_engine(),
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
    )


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that provides a database session per request.

    The session is automatically closed after the request completes.
    """
    session_factory = get_session_factory()
    db = session_factory()
    try:
        yield db
    finally:
        db.close()
