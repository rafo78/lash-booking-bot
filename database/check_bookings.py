import asyncio

from sqlalchemy import text

from database.database import engine


async def check_bookings():
    async with engine.connect() as connection:
        result = await connection.execute(
            text(
                "SELECT name FROM sqlite_master "
                "WHERE type='table' AND name='bookings'"
            )
        )

        table = result.scalar_one_or_none()

        if table:
            print("✅ Таблица bookings существует!")
        else:
            print("❌ Таблица bookings НЕ найдена!")


if __name__ == "__main__":
    asyncio.run(check_bookings())