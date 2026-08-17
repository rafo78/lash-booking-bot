import asyncio
import os

from aiogram import Bot, Dispatcher
from dotenv import load_dotenv

from bot.handlers.start import router as start_router
from bot.handlers.services import router as services_router
from database.database import init_database


load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise RuntimeError(
        "BOT_TOKEN не найден в файле .env"
    )


dp = Dispatcher()

dp.include_router(start_router)
dp.include_router(services_router)


async def main():
    print("Запускаю базу данных...")

    await init_database()

    print("База данных готова")
    print("Запускаю Telegram-бота...")

    bot = Bot(token=BOT_TOKEN)

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())