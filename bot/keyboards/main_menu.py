from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def get_main_menu(role: str = "client") -> ReplyKeyboardMarkup:
    keyboard = [
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
    ]

    if role == "master":
        keyboard.append(
            [
                KeyboardButton(
                    text="👩‍💼 Кабинет мастера"
                )
            ]
        )

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
    )