import datetime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey
from typing import List


class Base(DeclarativeBase):
    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        default=datetime.datetime.now()
    )


class User(Base):
    __tablename__ = "users"
    telegram_id: Mapped[int] = mapped_column(unique=True, nullable=False)
    username: Mapped[str] = mapped_column()
    full_name: Mapped[str] = mapped_column()
    is_admin: Mapped[bool] = mapped_column(default=False)
    targets: Mapped[List["Target"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class TariffPlan(Base):
    __tablename__ = "tariff_plans"
    name: Mapped[str] = mapped_column(unique=True)
    price: Mapped[float] = mapped_column(default=100)
    targets_limit: Mapped[int] = mapped_column(default=1)
    description: Mapped[str] = mapped_column()
    is_active: Mapped[bool] = mapped_column(default=True)


DEFAULT_TARGET_NAME = "Новая цель"


class Target(Base):
    __tablename__ = "targets"
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    user: Mapped[User] = relationship(back_populates="targets")
    title: Mapped[str] = mapped_column(default=DEFAULT_TARGET_NAME)
    url: Mapped[str] = mapped_column(nullable=False)


class Subscription(Base):
    """Not implemented yet"""

    __tablename__ = "subscriptions"
