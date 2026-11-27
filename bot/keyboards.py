from vkbottle import Keyboard, KeyboardButtonColor, Text, Callback


def get_main_keyboard() -> str:
    """Главная клавиатура бота (под сообщением)."""
    kb = Keyboard(one_time=False, inline=False)
    kb.add(Text("📋 Мои списки"), color=KeyboardButtonColor.PRIMARY)
    kb.add(Text("➕ Создать список"), color=KeyboardButtonColor.POSITIVE)
    return kb.get_json()


def get_lists_keyboard(wishlists: list) -> str:
    """Клавиатура со списком вишлистов пользователя."""
    kb = Keyboard(one_time=False, inline=False)
    for wl in wishlists:
        # Каждая кнопка ведет на просмотр конкретного списка
        kb.add(Text(f"📂 {wl.title}"), color=KeyboardButtonColor.SECONDARY)
        kb.row()  # Переход на новую строку для каждого списка
    kb.add(Text("🔙 Назад в меню"), color=KeyboardButtonColor.NEGATIVE)
    return kb.get_json()