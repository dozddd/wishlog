from vkbottle import BaseMiddleware
from vkbottle.bot import Message
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


class DatabaseSessionMiddleware(BaseMiddleware[Message]):
    # фабрика для создания сессий базы данных
    session_factory: async_sessionmaker[AsyncSession] | None = None

    async def pre(self):
        # проверяем, настроена ли фабрика сессий
        if self.session_factory is None:
            raise RuntimeError("Фабрика сессий БД не настроена")

        # создаём новую сессию
        self.db_session = self.session_factory()

        # передаём сессию в контекст хендлера
        self.send({"db_session": self.db_session})

    async def post(self):
        # получаем созданную сессию
        db_session = getattr(self, "db_session", None)

        # закрываем сессию после обработки сообщения
        if db_session is not None:
            await db_session.close()


def register_database_middleware(bot, session_factory):
    # передаём фабрику сессий в middleware
    DatabaseSessionMiddleware.session_factory = session_factory

    # подключаем middleware к обработчикам сообщений
    bot.labeler.message_view.register_middleware(DatabaseSessionMiddleware)
