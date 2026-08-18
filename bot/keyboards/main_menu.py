from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def get_main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📅 Записаться"),
                KeyboardButton(text="💰 Услуги и цены"),
            ],
            [
                KeyboardButton(text="📸 Портфолио"),
                KeyboardButton(text="📍 Адреса"),
            ],
            [
                KeyboardButton(text="📋 Мои записи"),
                KeyboardButton(text="ℹ️ О сервисе"),
            ],
            [
                KeyboardButton(text="👩 О Полечке"),
            ],
        ],
        resize_keyboard=True,
    )