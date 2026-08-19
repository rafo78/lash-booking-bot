import asyncio

from sqlalchemy import text

from database.database import engine


async def migrate():
    async with engine.begin() as connection:
        result = await connection.execute(
            text("PRAGMA table_info(services)")
        )

        columns = result.fetchall()
        column_names = [column[1] for column in columns]

        if "category" in column_names:
            print("ℹ️ Колонка category уже существует.")
            return

        await connection.execute(
            text(
                """
                ALTER TABLE services
                ADD COLUMN category VARCHAR(100)
                NOT NULL
                DEFAULT 'Другое'
                """
            )
        )

        print("✅ Колонка category успешно добавлена!")


if __name__ == "__main__":
    asyncio.run(migrate())