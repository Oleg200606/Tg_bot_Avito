from ..database_engine import new_session
from ..models import TariffPlan
from sqlalchemy import select, insert

CURRENCY = "руб."


def get_tariff_plans() -> list[TariffPlan]:
    with new_session() as session:
        statement = select(TariffPlan).where(TariffPlan.is_active)
        plans = session.scalars(statement)
        return list(plans)


def format_tariff_plan(plan: TariffPlan) -> str:
    return f"""\n• <b>{plan.name}</b> - {plan.price} {CURRENCY} - цели: {plan.targets_limit}
{plan.description}\n"""


def create_tariff_plan(name: str, price: int, targets_limit: int, description: str):
    if price <= 0:
        raise ValueError("price can't be lower or equal to zero")
    if targets_limit <= 0:
        raise ValueError("targets limit can't be lower or equal to zero")

    with new_session() as session:
        statement = insert(TariffPlan).values(
            name=name,
            price=price,
            targets_limit=targets_limit,
            description=description,
        )
        session.execute(statement)
        session.commit()
