from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    telegram_id: Mapped[int] = mapped_column(
        BigInteger,
        unique=True,
        index=True,
        nullable=False,
    )

    username: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    first_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    phone: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    role: Mapped[str] = mapped_column(
        String(20),
        default="client",
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    bookings: Mapped[list["Booking"]] = relationship(
        back_populates="user",
    )


class Master(Base):
    __tablename__ = "masters"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    city: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    address: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    work_start: Mapped[str] = mapped_column(
        String(5),
        nullable=False,
    )

    work_end: Mapped[str] = mapped_column(
        String(5),
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        default=True,
        nullable=False,
    )

    services: Mapped[list["Service"]] = relationship(
        back_populates="master",
        cascade="all, delete-orphan",
    )

    bookings: Mapped[list["Booking"]] = relationship(
        back_populates="master",
    )


class Service(Base):
    __tablename__ = "services"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    master_id: Mapped[int] = mapped_column(
        ForeignKey("masters.id"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    category: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="Другое",
    )

    price_from: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    price_to: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    duration_min: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    duration_max: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        default=True,
        nullable=False,
    )

    master: Mapped["Master"] = relationship(
        back_populates="services",
    )

    bookings: Mapped[list["Booking"]] = relationship(
        back_populates="service",
    )


class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    master_id: Mapped[int] = mapped_column(
        ForeignKey("masters.id"),
        nullable=False,
        index=True,
    )

    service_id: Mapped[int] = mapped_column(
        ForeignKey("services.id"),
        nullable=False,
        index=True,
    )

    booking_date: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        index=True,
    )

    booking_time: Mapped[str] = mapped_column(
        String(5),
        nullable=False,
    )

    duration_min: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    price: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    led: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        default="confirmed",
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    user: Mapped["User"] = relationship(
        back_populates="bookings",
    )

    master: Mapped["Master"] = relationship(
        back_populates="bookings",
    )

    service: Mapped["Service"] = relationship(
        back_populates="bookings",
    )
