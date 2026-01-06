from .config import Config
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

bot: Bot
dispatcher = Dispatcher()


def __init__(conf: Config):
    global bot, dispatcher
    bot = Bot(
        token=conf.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )


async def start_polling(conf: Config):
    from .routers import subscriptions, targets, tariff_plans, menu

    __init__(conf)
    dispatcher.include_routers(
        menu.router, subscriptions.router, targets.router, tariff_plans.router
    )
    await dispatcher.start_polling(bot)  # type: ignore
