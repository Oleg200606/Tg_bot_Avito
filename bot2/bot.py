from .config import Config
from aiogram.filters import Command
from aiogram.types import Message
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from .users import get_or_create_user
from .models import TariffPlan
from .database_engine import new_session
from sqlalchemy import select

bot: Bot
dispatcher = Dispatcher()


def __init__(conf: Config):
    global bot, dispatcher
    bot = Bot(
        token=conf.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )


def _get_tariff_plans() -> list[TariffPlan]:
    with new_session() as session:
        statement = select(TariffPlan).where(TariffPlan.is_active)
        plans = session.scalars(statement)
        return list(plans)


async def start_polling(conf: Config):
    from .routers import subscriptions, targets, tariff_plans

    __init__(conf)
    dispatcher.include_routers(
        subscriptions.router, targets.router, tariff_plans.router
    )
    await dispatcher.start_polling(bot)  # type: ignore


@dispatcher.message(Command("start"))
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
        __welcome_text(message.from_user.username or "неизвестный", _get_tariff_plans())
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

💎 <b>Тарифные планы:</b>"""
    for plan in tariff_plans:
        mesasge += _print_tariff_plan(plan)
    mesasge += """

<b>Запрос</b> - добавление одной ссылки.

Используйте кнопки ниже для навигации! 🚀"""
    return mesasge


def _print_tariff_plan(plan: TariffPlan) -> str:
    return f"""• <b>{plan.name}</b> - {plan.price}
{plan.description}"""
