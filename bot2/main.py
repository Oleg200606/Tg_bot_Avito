from .config import Config
from .logger import setup as logger_setup, get_logger
from .database_engine import create as create_engine
from .bot import start_polling


def create_tariffs():
    from .tariff_plans import create_tariff_plan, get_tariff_plans

    if len(get_tariff_plans()) > 0:
        return

    create_tariff_plan("Базовый", 199, 2, "Подходит для ознакомления с системой")
    create_tariff_plan("Повышенный", 399, 5, "Для тех кому нужно больше")
    create_tariff_plan(
        "Премиум",
        799,
        20,
        "Для тех, кто не готов на компромиссы. Включает больше привилегий в службе поддержки",
    )


async def main():

    conf = Config()

    logger_setup(conf)
    log = get_logger(__name__)

    log.info("Starting application")

    create_engine(conf)
    create_tariffs()

    await start_polling(conf)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
