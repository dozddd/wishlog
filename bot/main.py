import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from config import TOKEN

# логирование для отладки
logging.basicConfig(level=logging.INFO)

# инициализация
BOT_TOKEN = (TOKEN)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# хендлер на старт
@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer("Привет!")

# функция запуска
async def main():
    # Запускаем процесс получения обновлений (Long Polling)
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот выключен")