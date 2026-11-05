"""
ORM-модели базы данных.

ORM (Object-Relational Mapping) позволяет работать с таблицами БД
как с обычными Python-классами: один класс = одна таблица,
один объект = одна строка в таблице.

Связи между таблицами:
    User 1---N WishList   (у пользователя может быть много списков)
    WishList 1---N Item   (в списке может быть много подарков)
    User 1---N Item       (пользователь может забронировать много подарков)
"""
from datetime import datetime

from sqlalchemy import BigInteger, ForeignKey, Numeric, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """
    Базовый класс для всех моделей.
    SQLAlchemy по нему узнаёт, какие таблицы нужно создать в БД.
    """
    pass


class User(Base):
    """Пользователь Telegram, который хотя бы раз написал боту."""

    __tablename__ = "users"  # имя таблицы в БД

    # Первичный ключ: уникальный номер строки, генерируется автоматически
    id: Mapped[int] = mapped_column(primary_key=True)

    # Telegram ID пользователя. Он может быть очень большим числом,
    # поэтому BigInteger. unique=True - два пользователя с одним tg_id невозможны,
    # index=True - ускоряет поиск по этому полю (мы ищем по нему постоянно).
    tg_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)

    # У пользователя может не быть @username, поэтому "str | None" и nullable=True
    username: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # Отображаемое имя, которое мы показываем другим пользователям
    full_name: Mapped[str] = mapped_column(String(128))

    # server_default=func.now(): дату проставляет сама БД в момент создания строки
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    # Обратная сторона связи: user.wishlists вернёт все списки пользователя.
    # cascade="all, delete-orphan": при удалении пользователя
    # удалятся и все его списки.
    wishlists: Mapped[list["WishList"]] = relationship(
        back_populates="owner", cascade="all, delete-orphan"
    )


class WishList(Base):
    """Список желаний. Принадлежит одному пользователю."""

    __tablename__ = "wishlists"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Внешний ключ: ссылка на users.id. ondelete="CASCADE" означает,
    # что при удалении пользователя БД сама удалит его списки.
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))

    title: Mapped[str] = mapped_column(String(128))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    # wishlist.owner вернёт объект User, которому принадлежит список
    owner: Mapped["User"] = relationship(back_populates="wishlists")

    # wishlist.items вернёт все подарки списка.
    # order_by: подарки всегда идут от самого желанного (priority=2) к обычному (0).
    items: Mapped[list["Item"]] = relationship(
        back_populates="wishlist",
        cascade="all, delete-orphan",  # удалили список - удалились и подарки
        order_by="Item.priority.desc()",
    )


class Item(Base):
    """Один подарок внутри списка."""

    __tablename__ = "items"

    id: Mapped[int] = mapped_column(primary_key=True)

    # К какому списку относится подарок
    wishlist_id: Mapped[int] = mapped_column(ForeignKey("wishlists.id", ondelete="CASCADE"))

    title: Mapped[str] = mapped_column(String(128))

    # Необязательные поля: пользователь может пропустить их при добавлении
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    url: Mapped[str | None] = mapped_column(String(512), nullable=True)

    # Numeric(10, 2): до 10 цифр, из них 2 после запятой (деньги)
    price: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)

    # Приоритет: 0 - обычный, 1 - желанный, 2 - мечта
    priority: Mapped[int] = mapped_column(default=0)

    # --- Бронирование ---
    # Владелец списка эти поля никогда не видит. Но скрываем мы их не здесь,
    # а в сервисном слое: в БД данные должны храниться, чтобы бронь
    # можно было показать другим гостям и снять.
    is_booked: Mapped[bool] = mapped_column(default=False)

    # Кто забронировал. ondelete="SET NULL": если этот пользователь удалится,
    # подарок не пропадёт, просто бронь обнулится.
    booked_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    wishlist: Mapped["WishList"] = relationship(back_populates="items")

    # У Item два внешних ключа на users? Нет, только один (booked_by_id),
    # но foreign_keys указываем явно, чтобы SQLAlchemy не гадал, по какому
    # полю строить связь.
    booked_by: Mapped["User | None"] = relationship(foreign_keys=[booked_by_id])