import asyncio

from sqlalchemy import delete, select

from database.database import async_session, init_database
from database.models import Master, Service


SERVICES = [
    # Коррекция
    {
        "category": "Коррекция",
        "name": "Коррекция классический объём 1D",
        "price": 1400,
        "duration": 50,
    },
    {
        "category": "Коррекция",
        "name": "Коррекция объём 1,5D",
        "price": 1500,
        "duration": 50,
    },
    {
        "category": "Коррекция",
        "name": "Коррекция объём 2D",
        "price": 1700,
        "duration": 60,
    },
    {
        "category": "Коррекция",
        "name": "Коррекция объём 2,5D",
        "price": 1800,
        "duration": 60,
    },
    {
        "category": "Коррекция",
        "name": "Коррекция объём 3D",
        "price": 2000,
        "duration": 75,
    },
    {
        "category": "Коррекция",
        "name": "Коррекция объём 3,5D",
        "price": 2100,
        "duration": 75,
    },
    {
        "category": "Коррекция",
        "name": "Коррекция объём 4–6D",
        "price": 2300,
        "duration": 90,
    },

    # Наращивание
    {
        "category": "Наращивание",
        "name": "Наращивание классический объём 1D",
        "price": 2300,
        "duration": 100,
    },
    {
        "category": "Наращивание",
        "name": "Наращивание объём 1,5D",
        "price": 2400,
        "duration": 110,
    },
    {
        "category": "Наращивание",
        "name": "Наращивание объём 2D",
        "price": 2600,
        "duration": 120,
    },
    {
        "category": "Наращивание",
        "name": "Наращивание объём 2,5D",
        "price": 2700,
        "duration": 120,
    },
    {
        "category": "Наращивание",
        "name": "Наращивание объём 3D",
        "price": 2900,
        "duration": 135,
    },
    {
        "category": "Наращивание",
        "name": "Наращивание объём 3,5D",
        "price": 3000,
        "duration": 135,
    },
    {
        "category": "Наращивание",
        "name": "Наращивание объём 4–6D / Голливуд",
        "price": 3200,
        "duration": 140,
    },
    {
        "category": "Наращивание",
        "name": "Наращивание ресниц «Уголки»",
        "price": 1800,
        "duration": 40,
    },
    {
        "category": "Наращивание",
        "name": "Наращивание ресниц Экспресс 1–2D",
        "price": 1500,
        "duration": 60,
    },
    {
        "category": "Наращивание",
        "name": "Наращивание ресниц Экспресс 3–4D",
        "price": 1800,
        "duration": 80,
    },

    # Снятие
    {
        "category": "Снятие",
        "name": "Снятие наращенных ресниц без последующего наращивания",
        "price": 500,
        "duration": 15,
    },
    {
        "category": "Снятие",
        "name": "Снятие ресниц от другого мастера при наращивании",
        "price": 200,
        "duration": 10,
    },
]


async def seed_data():
    await init_database()

    async with async_session() as session:
        result = await session.execute(
            select(Master).where(
                Master.name == "Полечка"
            )
        )

        master = result.scalar_one_or_none()

        if master is None:
            master = Master(
                name="Полечка",
                city="Рязань",
                address="ул. Чапаева, 59",
                work_start="10:00",
                work_end="20:00",
                is_active=True,
            )

            session.add(master)
            await session.flush()

            print("✅ Мастер Полечка добавлена.")
        else:
            print("ℹ️ Мастер Полечка уже существует.")

        await session.execute(
            delete(Service).where(
                Service.master_id == master.id
            )
        )

        services = []

        for item in SERVICES:
            services.append(
                Service(
                    master_id=master.id,
                    category=item["category"],
                    name=item["name"],
                    price_from=item["price"],
                    price_to=item["price"],
                    duration_min=item["duration"],
                    duration_max=item["duration"],
                    is_active=True,
                )
            )

        session.add_all(services)

        await session.commit()

        print(f"✅ Добавлено услуг: {len(services)}")


if __name__ == "__main__":
    asyncio.run(seed_data())