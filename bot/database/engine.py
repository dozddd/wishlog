"""
Инициализация асинхронного движка SQLAlchemy и фабрики сессий.
"""
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from bot.database.models import Base


def create_engine_and_sessionmaker(database_url: str):
    engine = create_async_engine(database_url, echo=False)
    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    return engine, session_factory


async def init_models(engine) -> None:
    """Создаёт таблицы, если их ещё нет. Для продакшена лучше использовать Alembic-миграции."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
