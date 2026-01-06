from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from ..users import get_or_create_user
from ..tariff_plans import get_tariff_plans
from ..models import TariffPlan
from .common import format_tariff_plan
from ..keyboards import get_main_menu

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message):
    if not message.from_user:
        return
    user = get_or_create_user(
        message.from_user.id,
        message.from_user.username or "",
        message.from_user.full_name,
    )
    if not user:
        await message.answer("Что-то пошло не так")

    await message.answer(
        __welcome_text(message.from_user.username or "неизвестный", get_tariff_plans()),
        reply_markup=get_main_menu(message.chat.id),
    )


def __welcome_text(username: str, tariff_plans: list[TariffPlan]):
    mesasge = f"""
👋 Привет, {username}!

🤖 Я бот для управления подписками с Яндекс Кассой.

✨ <b>Доступные функции:</b>
• Безопасная оплата через Яндекс Кассу
• Добавление ссылок с учетом лимита
• Просмотр статистики и истории
• Автоматическое обновление подписок

💎 <b>Тарифные планы:</b>
"""
    for plan in tariff_plans:
        mesasge += format_tariff_plan(plan)
    mesasge += """

<b>Запрос</b> - добавление одной ссылки.

Используйте кнопки ниже для навигации! 🚀"""
    return mesasge
