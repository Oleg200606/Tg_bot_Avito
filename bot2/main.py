async def main():
    from .config import Config
    from .logger import setup as logger_setup, get_logger
    from .database_engine import create
    from .bot import start_polling

    conf = Config()

    logger_setup(conf)
    log = get_logger(__name__)

    create(conf)

    await start_polling(conf)

if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
