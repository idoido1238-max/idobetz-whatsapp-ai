"""
Database configuration using SQLAlchemy async.
Engine is created lazily to allow test isolation via environment variables.
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.config import settings


def _make_async_url(url: str) -> str:
    """Convert sync DB URL to async driver URL."""
    return (
        url
        .replace("postgresql://", "postgresql+asyncpg://")
        .replace("postgres://", "postgresql+asyncpg://")
    )


def _build_engine_kwargs(url: str) -> dict:
    """Build engine kwargs - SQLite doesn't support pool_size/max_overflow."""
    kwargs: dict = {"echo": settings.DEBUG, "future": True}
    if not url.startswith("sqlite"):
        kwargs["pool_size"] = settings.DATABASE_POOL_SIZE
        kwargs["max_overflow"] = settings.DATABASE_MAX_OVERFLOW
    return kwargs


def _create_engine():
    db_url = _make_async_url(settings.DATABASE_URL)
    return create_async_engine(db_url, **_build_engine_kwargs(db_url))


# Lazy engine – created on first access so tests can override DATABASE_URL via env
engine = _create_engine()

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db():
    """Dependency: get DB session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
