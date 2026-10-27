"""
DeviationIQ — Async Database Engine & Session Factory

Uses SQLAlchemy 2.0 async engine with connection pooling and SQLite WAL optimization.
"""

from __future__ import annotations

import logging
from sqlalchemy import event, text
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings

logger = logging.getLogger("deviationiq.database")
settings = get_settings()

is_sqlite = settings.database_url.startswith("sqlite")
engine_kwargs = {"echo": False}

if not is_sqlite:
    engine_kwargs.update({
        "pool_pre_ping": True,
        "pool_size": 20,
        "max_overflow": 10,
        "pool_timeout": 30,
        "pool_recycle": 1800,
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


@event.listens_for(Engine, "connect")
def configure_sqlite_pragmas(dbapi_connection, connection_record):
    """
    Enables Write-Ahead Logging (WAL) and busy timeout for high-concurrency SQLite operations.
    Prevents 'database is locked' errors during concurrent multi-user workloads.
    """
    try:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.execute("PRAGMA synchronous=NORMAL;")
        cursor.execute("PRAGMA busy_timeout=10000;")
        cursor.close()
    except Exception:
        # Ignore for non-sqlite engines
        pass


def run_auto_migrations(sync_conn):
    """
    Safely inspects existing tables and applies ALTER TABLE ADD COLUMN
    for any missing schema columns in SQLite.
    Prevents schema mismatch crashes when models evolve without full database re-creation.
    """
    from app.models import Base

    dialect_name = sync_conn.dialect.name
    if dialect_name == "sqlite":
        for table_name, table in Base.metadata.tables.items():
            try:
                res = sync_conn.execute(text(f"PRAGMA table_info({table_name})"))
                existing_cols = {row[1] for row in res.fetchall()}
                if not existing_cols:
                    continue
                for col in table.columns:
                    if col.name not in existing_cols:
                        type_str = col.type.compile(sync_conn.dialect)
                        sync_conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {col.name} {type_str}"))
                        logger.info("Auto-migrated table %s: added column %s (%s)", table_name, col.name, type_str)
            except Exception as e:
                logger.warning("Auto-migration check for table %s skipped: %s", table_name, e)


async def init_sqlite_fallback():
    """Initializes local SQLite engine if PostgreSQL is unreachable."""
    global engine, async_session_factory
    from app.models import Base
    from app.services.security import seed_default_users

    logger.info("Switching to local SQLite engine (sqlite+aiosqlite:///./deviationiq.db)...")
    engine = create_async_engine("sqlite+aiosqlite:///./deviationiq.db", echo=False)
    async_session_factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.run_sync(run_auto_migrations)
    logger.info("SQLite database tables verified/created (deviationiq.db).")

    # Seed default clinical users
    async with async_session_factory() as session:
        await seed_default_users(session)


async def check_db_health(session: Optional[AsyncSession] = None) -> bool:
    """Execute lightweight probe query to verify database liveness."""
    try:
        if session is not None:
            result = await session.execute(text("SELECT 1"))
            return result.scalar() == 1
        async with async_session_factory() as s:
            result = await s.execute(text("SELECT 1"))
            return result.scalar() == 1
    except Exception as e:
        logger.error("Database health check failed: %s", e)
        return False


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
