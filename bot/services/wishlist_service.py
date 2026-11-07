"""
Сервисный слой: вся бизнес-логика, которая не является простым CRUD,
живёт здесь. Хендлеры (VK-слой) не должны напрямую трогать репозитории -
только через сервис.
"""
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models import Item, User, WishList
from bot.repositories.item_repo import ItemRepository
from bot.repositories.user_repo import UserRepository
from bot.repositories.wishlist_repo import WishListRepository


class NotOwnerError(Exception):
    """Пользователь пытается изменить чужой список."""


class CannotBookOwnItemError(Exception):
    """Владелец списка пытается забронировать собственный подарок."""


class AlreadyBookedError(Exception):
    """Подарок уже забронирован другим пользователем."""


@dataclass
class ItemView:
    """
    То, что реально видит пользователь. Ключевая идея всего проекта:
    если запрашивает владелец списка - поля бронирования всегда скрыты (None/False),
    даже если в БД они заполнены.
    """

    item: Item
    is_booked_visible: bool
    booked_by_name: str | None


class WishlistService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.users = UserRepository(session)
        self.wishlists = WishListRepository(session)
        self.items = ItemRepository(session)

    # ---------- пользователи ----------

    async def register_user(self, vk_id: int, username: str | None, full_name: str) -> User:
        return await self.users.get_or_create(vk_id, username, full_name)

    # ---------- списки ----------

    async def create_wishlist(self, owner_vk_id: int, title: str) -> WishList:
        owner = await self.users.get_by_vk_id(owner_vk_id)
        if owner is None:
            raise ValueError("Пользователь не зарегистрирован")
        return await self.wishlists.create(owner.id, title)

    async def get_own_wishlists(self, owner_vk_id: int) -> list[WishList]:
        owner = await self.users.get_by_vk_id(owner_vk_id)
        if owner is None:
            return []
        return await self.wishlists.get_all_by_owner(owner.id)

    async def delete_wishlist(self, wishlist_id: int, requester_vk_id: int) -> None:
        wishlist = await self.wishlists.get_by_id(wishlist_id)
        if wishlist is None:
            return
        requester = await self.users.get_by_vk_id(requester_vk_id)
        if requester is None or wishlist.owner_id != requester.id:
            raise NotOwnerError()
        await self.wishlists.delete(wishlist)

    # ---------- подарки ----------

    async def add_item(
        self,
        wishlist_id: int,
        requester_vk_id: int,
        title: str,
        description: str | None,
        url: str | None,
        price: float | None,
        priority: int = 0,
    ) -> Item:
        wishlist = await self.wishlists.get_by_id(wishlist_id)
        if wishlist is None:
            raise ValueError("Список не найден")
        requester = await self.users.get_by_vk_id(requester_vk_id)
        if requester is None or wishlist.owner_id != requester.id:
            raise NotOwnerError()
        return await self.items.create(wishlist_id, title, description, url, price, priority)

    async def remove_item(self, item_id: int, requester_vk_id: int) -> None:
        item = await self.items.get_by_id(item_id)
        if item is None:
            return
        wishlist = await self.wishlists.get_by_id(item.wishlist_id)
        requester = await self.users.get_by_vk_id(requester_vk_id)
        if requester is None or wishlist is None or wishlist.owner_id != requester.id:
            raise NotOwnerError()
        await self.items.delete(item)

    # ---------- бронирование (ключевая фича проекта) ----------

    async def book_item(self, item_id: int, requester_vk_id: int) -> Item:
        item = await self.items.get_by_id(item_id)
        if item is None:
            raise ValueError("Подарок не найден")
        wishlist = await self.wishlists.get_by_id(item.wishlist_id)
        requester = await self.users.get_by_vk_id(requester_vk_id)
        if requester is None:
            raise ValueError("Пользователь не зарегистрирован")
        if wishlist.owner_id == requester.id:
            raise CannotBookOwnItemError()
        if item.is_booked and item.booked_by_id != requester.id:
            raise AlreadyBookedError()
        return await self.items.set_booking(item, requester.id)

    async def unbook_item(self, item_id: int, requester_vk_id: int) -> Item:
        item = await self.items.get_by_id(item_id)
        if item is None:
            raise ValueError("Подарок не найден")
        requester = await self.users.get_by_vk_id(requester_vk_id)
        if requester is None or item.booked_by_id != requester.id:
            raise NotOwnerError()
        return await self.items.set_booking(item, None)

    # ---------- просмотр с учётом видимости брони ----------

    async def get_wishlist_for_viewer(
            self, wishlist_id: int, viewer_vk_id: int
    ) -> tuple[WishList, list[ItemView]] | None:
        """
        Возвращает список и подарки в виде ItemView, где статус брони
        скрыт, если смотрит владелец. Именно эта функция гарантирует
        сохранение сюрприза - используйте её всегда вместо прямого
        обращения к wishlist.items.
        """
        wishlist = await self.wishlists.get_by_id(wishlist_id)
        if wishlist is None:
            return None
        viewer = await self.users.get_by_vk_id(viewer_vk_id)
        is_owner = viewer is not None and viewer.id == wishlist.owner_id

        views: list[ItemView] = []
        for item in wishlist.items:
            if is_owner:
                views.append(ItemView(item=item, is_booked_visible=False, booked_by_name=None))
            else:
                booked_name = None
                if item.is_booked and item.booked_by is not None:
                    booked_name = item.booked_by.full_name
                views.append(
                    ItemView(
                        item=item,
                        is_booked_visible=item.is_booked,
                        booked_by_name=booked_name,
                    )
                )
        return wishlist, views