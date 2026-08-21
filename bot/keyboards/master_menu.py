from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def get_master_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📅 Мои записи"),
                KeyboardButton(text="👥 Мои клиенты"),
            ],
            [
                KeyboardButton(text="💅 Мои услуги"),
                KeyboardButton(text="🕐 Расписание"),
            ],
            [
                KeyboardButton(text="⚙️ Настройки"),
            ],
            [
                KeyboardButton(text="🔙 Главное меню"),
            ],
        ],
        resize_keyboard=True,
    )