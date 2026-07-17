import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Default to an in-memory SQLite if no URL is provided, but typically this is overridden by env vars
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")

# SQLAlchemy engine
engine = create_async_engine(
    DATABASE_URL,
    echo=os.getenv("ECHO_SQL", "False").lower() in ("true", "1", "yes"),
    future=True,
    pool_size=int(os.getenv("POOL_SIZE", "5")) if not DATABASE_URL.startswith("sqlite") else None,
    max_overflow=int(os.getenv("MAX_OVERFLOW", "10")) if not DATABASE_URL.startswith("sqlite") else None,
)

# Async session factory
AsyncSessionFactory = sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession
)

async def get_db_session() -> AsyncSession:
    """Dependency to provide a database session."""
    async with AsyncSessionFactory() as session:
        yield session
