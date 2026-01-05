from aiogram import Router, F
from bot2.keyboards import get_subscription_plans
from aiogram.types import Message
from ..database_engine import new_session
from sqlalchemy import select

from ..models import TariffPlan

router = Router()


def _get_tariff_plans() -> list[TariffPlan]:
    with new_session() as session:
        statement = select(TariffPlan).where(TariffPlan.is_active)
        plans = session.scalars(statement)
        return list(plans)


def _print_tariff_plan(plan: TariffPlan) -> str:
    return f"""• <b>{plan.name}</b> - {plan.price}
{plan.description}"""


@router.message(F.text == "💎 Купить подписку")
async def buy_subscription(message: Message):

    text = """💎 <b>Выберите тарифный план:</b>"""

    plans = _get_tariff_plans()
    for tariff in plans:
        text += _print_tariff_plan(tariff)

    text += "\n\nВыберите подходящий план:"

    await message.answer(text, reply_markup=get_subscription_plans(list(plans)))
