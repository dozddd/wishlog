"""
Юнит-тесты бизнес-логики. Главный сценарий, который важно защитить тестами -
сокрытие статуса бронирования от владельца списка.
"""
import pytest

from bot.services.wishlist_service import (
    AlreadyBookedError,
    CannotBookOwnItemError,
    NotOwnerError,
    WishlistService,
)


@pytest.mark.asyncio
async def test_create_wishlist_and_add_item(service: WishlistService):
    await service.register_user(vk_id=1, username="alice", full_name="Alice")
    wishlist = await service.create_wishlist(owner_vk_id=1, title="ДР")
    item = await service.add_item(
        wishlist_id=wishlist.id,
        requester_vk_id=1,
        title="Наушники",
        description=None,
        url=None,
        price=5000,
    )
    assert item.title == "Наушники"
    assert item.is_booked is False


@pytest.mark.asyncio
async def test_owner_never_sees_booking_status(service: WishlistService):
    await service.register_user(vk_id=1, username="alice", full_name="Alice")
    await service.register_user(vk_id=2, username="bob", full_name="Bob")
    wishlist = await service.create_wishlist(owner_vk_id=1, title="ДР")
    item = await service.add_item(
        wishlist_id=wishlist.id,
        requester_vk_id=1,
        title="Книга",
        description=None,
        url=None,
        price=None,
    )

    await service.book_item(item.id, requester_vk_id=2)

    _, owner_view = await service.get_wishlist_for_viewer(wishlist.id, viewer_vk_id=1)
    assert owner_view[0].is_booked_visible is False
    assert owner_view[0].booked_by_name is None

    await service.register_user(vk_id=3, username="carl", full_name="Carl")
    _, guest_view = await service.get_wishlist_for_viewer(wishlist.id, viewer_vk_id=3)
    assert guest_view[0].is_booked_visible is True
    assert guest_view[0].booked_by_name == "Bob"


@pytest.mark.asyncio
async def test_cannot_book_own_item(service: WishlistService):
    await service.register_user(vk_id=1, username="alice", full_name="Alice")
    wishlist = await service.create_wishlist(owner_vk_id=1, title="ДР")
    item = await service.add_item(wishlist.id, 1, "Кружка", None, None, None)

    with pytest.raises(CannotBookOwnItemError):
        await service.book_item(item.id, requester_vk_id=1)


@pytest.mark.asyncio
async def test_cannot_double_book(service: WishlistService):
    await service.register_user(vk_id=1, username="alice", full_name="Alice")
    await service.register_user(vk_id=2, username="bob", full_name="Bob")
    await service.register_user(vk_id=3, username="carl", full_name="Carl")
    wishlist = await service.create_wishlist(owner_vk_id=1, title="ДР")
    item = await service.add_item(wishlist.id, 1, "Кружка", None, None, None)

    await service.book_item(item.id, requester_vk_id=2)
    with pytest.raises(AlreadyBookedError):
        await service.book_item(item.id, requester_vk_id=3)


@pytest.mark.asyncio
async def test_only_owner_can_delete_wishlist(service: WishlistService):
    await service.register_user(vk_id=1, username="alice", full_name="Alice")
    await service.register_user(vk_id=2, username="bob", full_name="Bob")
    wishlist = await service.create_wishlist(owner_vk_id=1, title="ДР")

    with pytest.raises(NotOwnerError):
        await service.delete_wishlist(wishlist.id, requester_vk_id=2)


@pytest.mark.asyncio
async def test_unbook_by_booker_frees_item(service: WishlistService):
    await service.register_user(vk_id=1, username="alice", full_name="Alice")
    await service.register_user(vk_id=2, username="bob", full_name="Bob")
    wishlist = await service.create_wishlist(owner_vk_id=1, title="ДР")
    item = await service.add_item(wishlist.id, 1, "Кружка", None, None, None)

    await service.book_item(item.id, requester_vk_id=2)
    freed = await service.unbook_item(item.id, requester_vk_id=2)

    assert freed.is_booked is False
    assert freed.booked_by_id is None


@pytest.mark.asyncio
async def test_only_booker_can_unbook(service: WishlistService):
    await service.register_user(vk_id=1, username="alice", full_name="Alice")
    await service.register_user(vk_id=2, username="bob", full_name="Bob")
    await service.register_user(vk_id=3, username="carl", full_name="Carl")
    wishlist = await service.create_wishlist(owner_vk_id=1, title="ДР")
    item = await service.add_item(wishlist.id, 1, "Кружка", None, None, None)

    await service.book_item(item.id, requester_vk_id=2)
    with pytest.raises(NotOwnerError):
        await service.unbook_item(item.id, requester_vk_id=3)