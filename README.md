# WishList Bot 🎁

Учебный проект: Telegram-бот для создания списков желаний и бронирования
подарков друзьями — так, чтобы владелец списка никогда не узнал, кто и что
ему подарит.

## Стек
Python 3.11+ · aiogram 3 · SQLAlchemy 2 (async) · SQLite (по умолчанию,
легко переключить на PostgreSQL) · Docker / docker-compose · pytest

## Быстрый запуск (локально)

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env            # впишите токен, полученный у @BotFather
python -m bot.main
```

## Запуск через Docker

```bash
cp .env.example .env
docker compose up --build
```

## Тесты

```bash
pytest -v
```

## Структура проекта

```
bot/
  config.py            загрузка настроек из .env
  database/
    models.py           ORM-модели: User, WishList, Item
    engine.py            движок SQLAlchemy + создание таблиц
  repositories/          CRUD-слой (прямая работа с БД)
  services/
    wishlist_service.py  бизнес-логика, в т.ч. сокрытие статуса брони
  states/forms.py         состояния FSM-диалогов
  keyboards/               inline/reply-клавиатуры
  handlers/                обработчики команд, сообщений и callback'ов
  middlewares.py           открытие сессии БД на каждый апдейт
  main.py                  точка входа
tests/                     юнит-тесты бизнес-логики (pytest + pytest-asyncio)
```

Подробное описание архитектуры, план разработки и распределение задач между
участниками команды — в сопроводительном отчёте (Word).

## Организация репозитория и задач

- `CONTRIBUTING.md` — правила веток, коммитов, Pull Request и код-стайла.
- `TASKS.md` — бэклог задач по неделям, готовый к переносу в GitHub Issues.
- `.github/ISSUE_TEMPLATE/` — шаблоны задач (`task.md`) и багов (`bug.md`).
- `.github/PULL_REQUEST_TEMPLATE.md` — чек-лист для каждого PR.
- `.github/workflows/ci.yml` — автозапуск тестов и линтера на каждый push/PR.
