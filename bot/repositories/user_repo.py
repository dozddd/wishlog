"""Repository-слой: вся работа с таблицей users живёт здесь и нигде больше."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models import User


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_vk_id(self, vk_id: int) -> User | None:
        result = await self.session.execute(select(User).where(User.vk_id == vk_id))
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: int) -> User | None:
        return await self.session.get(User, user_id)

    async def get_or_create(self, vk_id: int, username: str | None, full_name: str) -> User:
        user = await self.get_by_vk_id(vk_id)
        if user:
            changed = False
            if user.username != username:
                user.username = username
                changed = True
            if user.full_name != full_name:
                user.full_name = full_name
                changed = True
            if changed:
                await self.session.flush()
            return user

        user = User(vk_id=vk_id, username=username, full_name=full_name)
        self.session.add(user)
        await self.session.flush()
        return user