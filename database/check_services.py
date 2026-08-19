import asyncio

from sqlalchemy import select

from database.database import async_session
from database.models import Master, Service


async def check_services():
    async with async_session() as session:
        result = await session.execute(
            select(Master).where(
                Master.name == "Полечка"
            )
        )

        master = result.scalar_one_or_none()

        if master is None:
            print("❌ Полечка не найдена.")
            return

        result = await session.execute(
            select(Service)
            .where(Service.master_id == master.id)
            .order_by(Service.category, Service.id)
        )

        services = result.scalars().all()

        print()
        print(f"Мастер: {master.name}")
        print(f"Город: {master.city}")
        print(f"Адрес: {master.address}")
        print(f"График: {master.work_start} - {master.work_end}")
        print()
        print(f"Всего услуг: {len(services)}")
        print()

        current_category = None

        for service in services:
            if service.category != current_category:
                current_category = service.category
                print(f"--- {current_category} ---")

            print(
                f"{service.name} | "
                f"{service.price_from} ₽ | "
                f"{service.duration_min} мин"
            )


if __name__ == "__main__":
    asyncio.run(check_services())