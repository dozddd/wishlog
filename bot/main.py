import logging
from sqlalchemy import text

from vkbottle import Bot
from vkbottle.bot import Message
from vkbottle.dispatch.rules.base import TextRule

from bot.config import TOKEN, DATABASE_URL
from bot.database.engine import create_engine_and_sessionmaker
from bot.session import register_database_middleware
from bot.services.wishlist_service import WishlistService
from bot.keyboards import get_main_keyboard, get_lists_keyboard

# логирование для отладки
logging.basicConfig(level=logging.INFO)

# создаём бота
bot = Bot(token=TOKEN)

# создаём движок и фабрику сессий БД
engine, session_factory = create_engine_and_sessionmaker(DATABASE_URL)

# подключаем middleware для работы с сессиями
register_database_middleware(bot, session_factory)


# обработчик команды начала работы и регистрации
@bot.on.message(TextRule(["начать", "начни", "/start"], ignore_case=True))
async def cmd_start(message: Message, db_session):
    user_info = await message.get_user()
    vk_id = message.from_id
    
    full_name = f"{user_info.first_name} {user_info.last_name}" if user_info else "Пользователь"
    username = user_info.screen_name if user_info else None

    service = WishlistService(db_session)
    user = await service.register_user(vk_id=vk_id, username=username, full_name=full_name)
    await db_session.commit()

    await message.answer(
        f"Привет, {user.full_name}! 👋\n\n"
        "Добро пожаловать в **WishLog** — твой личный бот для списков желаний.\n"
        "Здесь ты можешь создавать вишлисты, добавлять подарки и делиться ими с друзьями, сохраняя интригу бронирования! 🎁\n\n"
        "Используй кнопки меню ниже для управления вишлистами.",
        keyboard=get_main_keyboard()
    )


# Обработчик кнопки "Мои списки"
@bot.on.message(TextRule(["📋 Мои списки"], ignore_case=True))
async def show_my_lists(message: Message, db_session):
    vk_id = message.from_id
    service = WishlistService(db_session)
    
    wishlists = await service.get_own_wishlists(vk_id)
    
    if not wishlists:
        await message.answer(
            "У тебя пока нет ни одного вишлиста. Нажми «➕ Создать список», чтобы добавить первый!",
            keyboard=get_main_keyboard()
        )
        return

    await message.answer(
        "📂 Твои списки желаний:",
        keyboard=get_lists_keyboard(wishlists)
    )


# Обработчик нажатия на конкретный вишлист (просмотр и генерация диплинка)
@bot.on.message(TextRule(ignore_case=True))
async def show_wishlist_details(message: Message, db_session):
    text_input = message.text
    
    # Если это название списка (начинается с иконки папки или совпадает со списком)
    if text_input.startswith("📂 "):
        list_title = text_input[2:].strip()
        vk_id = message.from_id
        service = WishlistService(db_session)
        
        wishlists = await service.get_own_wishlists(vk_id)
        target_list = next((wl for wl in wishlists if wl.title == list_title), None)
        
        if target_list:
            # Получаем ID группы для формирования правильного диплинка
            group_info = await bot.api.groups.get_by_id()
            group_domain = group_info[0].screen_name if group_info else f"club{group_info[0].id}"
            
            # Генерация диплинк-ссылки на список
            deeplink = f"https://vk.me/{group_domain}?ref=list_{target_list.id}"
            
            await message.answer(
                f"🎁 Вишлист: **{target_list.title}**\n\n"
                f"🔗 Ссылка для друзей (поделитесь ей, чтобы показать список):\n{deeplink}"
            )
            return


# Обработчик нажатия на кнопку "➕ Создать список"
@bot.on.message(TextRule(["➕ Создать список"], ignore_case=True))
async def ask_wishlist_title(message: Message):
    await message.answer(
        "📝 Введи название для нового вишлиста (например: «День рождения» или «Новый год»):"
    )


# Обработчик возврата в главное меню
@bot.on.message(TextRule(["🔙 Назад в меню"], ignore_case=True))
async def back_to_menu(message: Message):
    await message.answer("Главное меню:", keyboard=get_main_keyboard())


# Универсальный обработчик текстовых сообщений (создание вишлиста)
@bot.on.message()
async def handle_text_input(message: Message, db_session):
    text_input = message.text
    
    # Игнорируем стандартные кнопки меню и клики по спискам
    if text_input in ["📋 Мои списки", "➕ Создать список", "🔙 Назад в меню", "начать", "начни", "/start"] or text_input.startswith("📂 "):
        return

    vk_id = message.from_id
    service = WishlistService(db_session)
    
    try:
        await service.create_wishlist(owner_vk_id=vk_id, title=text_input)
        await db_session.commit()
        await message.answer(
            f"✅ Вишлист «{text_input}» успешно создан!",
            keyboard=get_main_keyboard()
        )
    except Exception:
        pass


if __name__ == "__main__":
    try:
        print("Бот запущен...")
        bot.run()
    except (KeyboardInterrupt, SystemExit):
        print("Бот выключен")