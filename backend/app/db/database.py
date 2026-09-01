"""
Database Connection & Async Session Lifecycle Management
"""
import sys
import logging
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool
from backend.app.core.config import get_settings

logger = logging.getLogger("recoverai.db")
settings = get_settings()

# Use NullPool during pytest execution to prevent asyncpg connection pool leakage across event loops
is_testing = "pytest" in sys.modules or settings.APP_ENV == "testing"

engine_kwargs = {"echo": False, "future": True}
if is_testing:
    engine_kwargs["poolclass"] = NullPool
else:
    engine_kwargs.update({"pool_size": 10, "max_overflow": 20, "pool_pre_ping": True})

# Create async engine for PostgreSQL using asyncpg driver
engine = create_async_engine(settings.async_database_url, **engine_kwargs)

# Async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

# Base model for declarative SQLAlchemy mappings
Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that provides an async database session per request.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """
    Utility function to initialize all database tables.
    """
    global engine, AsyncSessionLocal
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info(f"Database initialized successfully at {engine.url}")
    except Exception as err:
        logger.warning(f"PostgreSQL connection failed ({err}). Falling back to local SQLite database.")
        sqlite_url = "sqlite+aiosqlite:///./recovery_demo.db"
        engine = create_async_engine(sqlite_url, echo=False)
        AsyncSessionLocal = async_sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info(f"Fallback SQLite database initialized successfully at {sqlite_url}")

