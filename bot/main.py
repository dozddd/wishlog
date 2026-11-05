import logging
from vkbottle import Bot
from vkbottle.bot import Message
from vkbottle.dispatch.rules.base import TextRule
from config import TOKEN

# логирование для отладки
logging.basicConfig(level=logging.INFO)

# инициализация бота токеном сообщества ВК
BOT_TOKEN = TOKEN
bot = Bot(token=BOT_TOKEN)

# ignore_case=True отключает зависимость от регистра букв
@bot.on.message(TextRule(["начать", "начни"], ignore_case=True))
async def cmd_start(message: Message):
    # Отвечаем пользователю в ВК
    await message.answer("Привет!")

if __name__ == "__main__":
    try:
        # Запускаем бесконечный процесс получения обновлений (Long Polling)
        bot.run_forever()
    except (KeyboardInterrupt, SystemExit):
        print("Бот выключен")
