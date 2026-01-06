from aiogram import Router, F
from bot2.keyboards import get_subscription_plans
from aiogram.types import Message

from .common import format_tariff_plan
from ..tariff_plans import get_tariff_plans

router = Router()


@router.message(F.text == "💎 Купить подписку")
async def buy_subscription(message: Message):

    text = """💎 <b>Выберите тарифный план:</b>"""

    plans = get_tariff_plans()
    for tariff in plans:
        text += format_tariff_plan(tariff)

    text += "\n\nВыберите подходящий план:"

    await message.answer(text, reply_markup=get_subscription_plans(list(plans)))
