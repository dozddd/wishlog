import asyncio
import logging
import os

from vkbottle import Bot
from vkbottle.bot import Message
from vkbottle.dispatch.rules.base import TextRule

from bot.config import TOKEN, DATABASE_URL
from bot.database.engine import create_engine_and_sessionmaker, init_models
from bot.session import register_database_middleware
from bot.services.wishlist_service import WishlistService
from bot.keyboards import get_main_keyboard, get_lists_keyboard

logging.basicConfig(level=logging.INFO)

GROUP_ID = 242990571
IGNORED_TITLES = {
    "📋 мои списки",
    "➕ создать список",
    "🔙 назад в меню",
    "назад в меню",
    "начать",
    "начни",
    "/start",
}

bot = Bot(token=TOKEN)

print("Текущая рабочая директория:", os.getcwd())
print("Путь к файлу БД будет:", os.path.abspath("./wishlist.db"))

engine, session_factory = create_engine_and_sessionmaker(DATABASE_URL)
register_database_middleware(bot, session_factory)


@bot.on.message(TextRule(["начать", "начни", "/start"], ignore_case=True))
async def cmd_start(message: Message, db_session):
    user_info = await message.get_user()
    vk_id = message.from_id

    full_name = (
        f"{user_info.first_name} {user_info.last_name}"
        if user_info
        else "Пользователь"
    )
    username = user_info.screen_name if user_info else None

    service = WishlistService(db_session)
    user = await service.register_user(
        vk_id=vk_id, username=username, full_name=full_name
    )
    await db_session.commit()

    await message.answer(
        f"Привет, {user.full_name}! 👋\n\n"
        "Добро пожаловать в WishLog — твой личный бот для списков желаний.\n"
        "Здесь ты можешь создавать вишлисты, добавлять подарки и делиться ими с друзьями, "
        "сохраняя интригу бронирования! 🎁\n\n"
        "Используй кнопки меню ниже для управления вишлистами.",
        keyboard=get_main_keyboard(),
    )


@bot.on.message(TextRule(["📋 Мои списки", "мои списки"], ignore_case=True))
async def show_my_lists(message: Message, db_session):
    vk_id = message.from_id
    service = WishlistService(db_session)

    wishlists = await service.get_own_wishlists(vk_id)

    if not wishlists:
        await message.answer(
            "У тебя пока нет ни одного вишлиста. Нажми «➕ Создать список», чтобы добавить первый!",
            keyboard=get_main_keyboard(),
        )
        return

    await message.answer(
        "📂 Твои списки желаний:",
        keyboard=get_lists_keyboard(wishlists),
    )


@bot.on.message(TextRule(["➕ Создать список", "создать список"], ignore_case=True))
async def ask_wishlist_title(message: Message):
    await message.answer(
        "📝 Введи название для нового вишлиста (например: «День рождения» или «Новый год»):",
        keyboard=get_main_keyboard(),
    )


@bot.on.message(TextRule(["🔙 Назад в меню", "назад в меню"], ignore_case=True))
async def back_to_menu(message: Message):
    await message.answer("Главное меню:", keyboard=get_main_keyboard())


@bot.on.message()
async def show_wishlist_details(message: Message, db_session):
    text_input = (message.text or "").strip()
    if not text_input or text_input.lower() in IGNORED_TITLES:
        return

    # Выбор существующего списка из клавиатуры "📂 <название>"
    if text_input.startswith("📂 "):
        list_title = text_input[2:].strip()
        vk_id = message.from_id
        service = WishlistService(db_session)

        wishlists = await service.get_own_wishlists(vk_id)
        target_list = next((wl for wl in wishlists if wl.title == list_title), None)

        if target_list:
            group_domain = f"club{GROUP_ID}"
            try:
                group_info = await bot.api.groups.get_by_id(group_id=GROUP_ID)
                groups_list = getattr(group_info, "groups", None) or group_info
                if groups_list and getattr(groups_list[0], "screen_name", None):
                    group_domain = groups_list[0].screen_name
            except Exception as exc:
                logging.warning("Не удалось получить данные группы для диплинка: %s", exc)

            deeplink = f"https://vk.me/{group_domain}?ref=list_{target_list.id}"
            await message.answer(
                f"🎁 Вишлист: {target_list.title}\n\n"
                f"🔗 Ссылка для друзей (поделитесь ей, чтобы показать список):\n{deeplink}",
                keyboard=get_lists_keyboard(wishlists),
            )
            return

    # Создание нового вишлиста по введённому названию
    vk_id = message.from_id
    service = WishlistService(db_session)

    try:
        await service.create_wishlist(owner_vk_id=vk_id, title=text_input)
        await db_session.commit()
        await message.answer(
            f"✅ Вишлист «{text_input}» успешно создан!",
            keyboard=get_main_keyboard(),
        )
    except Exception as exc:
        logging.error("Ошибка при создании вишлиста: %s", exc)
        await message.answer(
            "❌ Не удалось создать вишлист. Попробуй другое название.",
            keyboard=get_main_keyboard(),
        )


if __name__ == "__main__":
    try:
        print("Инициализация базы данных...")
        asyncio.run(init_models(engine))
        print("Бот запущен...")
        bot.run()
    except (KeyboardInterrupt, SystemExit):
        print("Бот выключен")