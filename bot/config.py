import os
from dotenv import load_dotenv

# загружаем переменные из файла .env
load_dotenv()

# получаем токен сообщества ВКонтакте
TOKEN = os.getenv("TOKEN")

# получаем адрес базы данных
DATABASE_URL = os.getenv("DATABASE_URL")

# проверяем, что настройки заданы
if not TOKEN:
    raise ValueError("Не задан TOKEN в файле .env")

if not DATABASE_URL:
    raise ValueError("Не задан DATABASE_URL в файле .env")
