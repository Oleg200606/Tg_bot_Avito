import datetime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


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


class TariffPlan(Base):
    __tablename__ = "tariff_plans"
    name: Mapped[str] = mapped_column(unique=True)
    price: Mapped[float] = mapped_column(default=100)
    request_limit: Mapped[int] = mapped_column(default=1)
    description: Mapped[str] = mapped_column()
    is_active: Mapped[bool] = mapped_column(default=True)
