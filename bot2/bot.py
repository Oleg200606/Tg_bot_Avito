from bot2.keyboards import get_subscription_plans
from .config import Config
from aiogram.filters import Command
from aiogram.types import Message
from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from .users import get_or_create_user


bot: Bot
dispatcher = Dispatcher()


def __init__(conf: Config):
    global bot, dispatcher
    bot = Bot(
        token=conf.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )


async def start_polling(conf: Config):
    __init__(conf)
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

    await message.answer(__welcome_text(message.from_user.username or "неизвестный"))


def __welcome_text(username: str):
    return f"""
👋 Привет, {username}!

🤖 Я бот для управления подписками с Яндекс Кассой.

✨ <b>Доступные функции:</b>
• Безопасная оплата через Яндекс Кассу
• Добавление ссылок с учетом лимита
• Просмотр статистики и истории
• Автоматическое обновление подписок

💎 <b>Тарифные планы:</b>
1. 1 месяц (5 запросов) - 500₽
2. 3 месяца (15 запросов) - 1200₽
3. 6 месяцев (30 запросов) - 2000₽
4. 12 месяцев (60 запросов) - 3500₽

<b>Запрос</b> - добавление одной ссылки. Лимит обновляется при продлении.

Используйте кнопки ниже для навигации! 🚀"""


@dispatcher.message(F.text == "💎 Купить подписку")
async def buy_subscription(message: Message):
    from .database_engine import new_session
    from sqlalchemy import select
    from .models import TariffPlan

    text = """💎 <b>Выберите тарифный план:</b>"""

    with new_session() as session:
        statement = select(TariffPlan).where(TariffPlan.is_active)
        plans = session.scalars(statement)
        for tariff in plans:
            text += f"""• <b>{tariff.name}</b> - {tariff.price}
    {tariff.description}"""

    text += "\n\nВыберите подходящий план:"

    await message.answer(text, reply_markup=get_subscription_plans(list(plans)))
