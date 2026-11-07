"""Общие фикстуры для тестов: чистая in-memory БД на каждый тест."""
import pytest_asyncio

from bot.database.engine import create_engine_and_sessionmaker, init_models
from bot.services.wishlist_service import WishlistService


@pytest_asyncio.fixture
async def service():
    engine, session_factory = create_engine_and_sessionmaker("sqlite+aiosqlite:///:memory:")
    await init_models(engine)
    async with session_factory() as session:
        yield WishlistService(session)
        await session.commit()
    await engine.dispose()