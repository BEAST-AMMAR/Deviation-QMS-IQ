"""
DeviationIQ — Async Database Engine & Session Factory

Uses SQLAlchemy 2.0 async engine with asyncpg driver.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings

settings = get_settings()

is_sqlite = settings.database_url.startswith("sqlite")
engine_kwargs = {"echo": False}
if not is_sqlite:
    engine_kwargs.update({
        "pool_pre_ping": True,
        "pool_size": 5,
        "max_overflow": 10,
    })

engine = create_async_engine(
    settings.database_url,
    **engine_kwargs,
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_sqlite_fallback():
    """Initializes local SQLite engine if PostgreSQL is unreachable."""
    global engine, async_session_factory
    from app.models import Base
    import logging
    log = logging.getLogger(__name__)
    log.info("Switching to local SQLite engine (sqlite+aiosqlite:///./deviationiq.db)...")
    engine = create_async_engine("sqlite+aiosqlite:///./deviationiq.db", echo=False)
    async_session_factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    log.info("SQLite database tables verified/created (deviationiq.db).")


async def get_db() -> AsyncSession:
    """FastAPI dependency — yields an async session and commits/rollbacks."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
