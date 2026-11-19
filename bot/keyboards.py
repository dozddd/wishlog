from vkbottle import Keyboard, Text, Callback

def get_main_keyboard() -> str:
    """Главная клавиатура бота (под сообщением)."""
    kb = Keyboard(one_time=False, inline=False)
    kb.add(Text("📋 Мои списки"), color="primary")
    kb.add(Text("➕ Создать список"), color="positive")
    return kb.get_json()

def get_lists_keyboard(wishlists: list) -> str:
    """Клавиатура со списком вишлистов пользователя."""
    kb = Keyboard(one_time=False, inline=False)
    for wl in wishlists:
        # Каждая кнопка ведет на просмотр конкретного списка
        kb.add(Text(f"📂 {wl.title}"), color="secondary")
        kb.row() # Переход на новую строку для каждого списка
    kb.add(Text("🔙 Назад в меню"), color="negative")
    return kb.get_json()