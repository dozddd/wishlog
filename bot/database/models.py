"""
ORM-модели базы данных (SQLAlchemy 2.0, декларативный стиль с Mapped[]).

Схема:
    User 1---N WishList 1---N Item
    User 1---N Item (как "тот, кто забронировал")
"""
from datetime import datetime

from sqlalchemy import BigInteger, ForeignKey, Numeric, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    vk_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    full_name: Mapped[str] = mapped_column(String(128))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    wishlists: Mapped[list["WishList"]] = relationship(
        back_populates="owner", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} vk_id={self.vk_id} name={self.full_name!r}>"


class WishList(Base):
    __tablename__ = "wishlists"

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(128))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    owner: Mapped["User"] = relationship(back_populates="wishlists")
    items: Mapped[list["Item"]] = relationship(
        back_populates="wishlist", cascade="all, delete-orphan", order_by="Item.priority.desc()"
    )

    def __repr__(self) -> str:
        return f"<WishList id={self.id} title={self.title!r} owner_id={self.owner_id}>"


class Item(Base):
    """Один подарок внутри вишлиста."""

    __tablename__ = "items"

    id: Mapped[int] = mapped_column(primary_key=True)
    wishlist_id: Mapped[int] = mapped_column(ForeignKey("wishlists.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(128))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    price: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    priority: Mapped[int] = mapped_column(default=0)  # 0 - обычный, 1 - желанный, 2 - мечта

    # Бронирование. ВАЖНО: владелец списка никогда не должен видеть эти поля -
    # это скрывается на уровне сервисного слоя (см. services/wishlist_service.py),
    # а не на уровне БД, чтобы данные не терялись и бронь можно было снять.
    is_booked: Mapped[bool] = mapped_column(default=False)
    booked_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    wishlist: Mapped["WishList"] = relationship(back_populates="items")
    booked_by: Mapped["User | None"] = relationship(foreign_keys=[booked_by_id])

    def __repr__(self) -> str:
        return f"<Item id={self.id} title={self.title!r} booked={self.is_booked}>"