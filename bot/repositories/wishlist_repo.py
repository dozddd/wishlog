"""Repository-слой: работа с таблицей wishlists."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from bot.database.models import Item, WishList


class WishListRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, owner_id: int, title: str) -> WishList:
        wishlist = WishList(owner_id=owner_id, title=title)
        self.session.add(wishlist)
        await self.session.flush()
        return wishlist

    async def get_by_id(self, wishlist_id: int) -> WishList | None:
        # populate_existing=True гарантирует, что коллекция items будет
        # перезагружена из БД, даже если этот объект уже был в identity map
        # сессии (иначе после add_item() владелец увидит старый, пустой список).
        result = await self.session.execute(
            select(WishList)
            .where(WishList.id == wishlist_id)
            .options(selectinload(WishList.items).selectinload(Item.booked_by))
            .execution_options(populate_existing=True)
        )
        return result.scalar_one_or_none()

    async def get_all_by_owner(self, owner_id: int) -> list[WishList]:
        result = await self.session.execute(
            select(WishList).where(WishList.owner_id == owner_id).order_by(WishList.created_at)
        )
        return list(result.scalars().all())

    async def delete(self, wishlist: WishList) -> None:
        await self.session.delete(wishlist)
        await self.session.flush()