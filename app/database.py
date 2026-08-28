from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


class Base(DeclarativeBase):
    pass


engine = create_async_engine(settings.database_url, echo=False, future=True)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


async def init_db() -> None:
    """Dev/demo convenience only. Real deployments manage schema via Alembic
    migrations (see /alembic), not metadata.create_all."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
