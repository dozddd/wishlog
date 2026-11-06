"""Repository-слой: работа с таблицей items (подарки)."""
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models import Item


class ItemRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        wishlist_id: int,
        title: str,
        description: str | None = None,
        url: str | None = None,
        price: float | None = None,
        priority: int = 0,
    ) -> Item:
        item = Item(
            wishlist_id=wishlist_id,
            title=title,
            description=description,
            url=url,
            price=price,
            priority=priority,
        )
        self.session.add(item)
        await self.session.flush()
        return item

    async def get_by_id(self, item_id: int) -> Item | None:
        return await self.session.get(Item, item_id)

    async def delete(self, item: Item) -> None:
        await self.session.delete(item)
        await self.session.flush()

    async def set_booking(self, item: Item, booked_by_id: int | None) -> Item:
        item.is_booked = booked_by_id is not None
        item.booked_by_id = booked_by_id
        await self.session.flush()
        return item