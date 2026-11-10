from sqlalchemy import text
import logging

from vkbottle import Bot
from vkbottle.bot import Message
from vkbottle.dispatch.rules.base import TextRule

from bot.config import TOKEN, DATABASE_URL
from bot.database.engine import create_engine_and_sessionmaker
from bot.session import register_database_middleware


# логирование для отладки
logging.basicConfig(level=logging.INFO)

# создаём бота
bot = Bot(token=TOKEN)

# создаём движок и фабрику сессий БД
engine, session_factory = create_engine_and_sessionmaker(DATABASE_URL)

# подключаем middleware для работы с сессиями
register_database_middleware(bot, session_factory)


# обработчик команды начала работы
@bot.on.message(TextRule(["начать", "начни"], ignore_case=True))
async def cmd_start(message: Message, db_session):
    # проверяем подключение к базе данных
    result = await db_session.execute(text("SELECT 1"))

    # получаем результат запроса
    value = result.scalar()

    await message.answer(f"Подключение к БД работает: {value}")


if __name__ == "__main__":
    try:
        bot.run()
    except (KeyboardInterrupt, SystemExit):
        print("Бот выключен")