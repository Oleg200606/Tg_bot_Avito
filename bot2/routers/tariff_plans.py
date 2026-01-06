from aiogram import Router, F
from aiogram.types import Message
from .common import format_tariff_plan
from ..tariff_plans import get_tariff_plans
from bot2.keyboards import get_subscription_plans

router = Router()


@router.message(F.text == "Тарифы")
async def list_tariffs(message: Message):
    text = """💎 <b>Выберите тарифный план:</b>\n"""

    plans = get_tariff_plans()
    for tariff in plans:
        text += format_tariff_plan(tariff)

    text += "\n\nВыберите подходящий план:"

    await message.answer(text, reply_markup=get_subscription_plans(list(plans)))
