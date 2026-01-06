from sqlalchemy import create_engine, Engine, MetaData
from sqlalchemy.orm import Session, declarative_base
from .config import Config, DB_ENGINE_POSTGRES, DB_ENGINE_SQLITE
from .logger import get_logger

engine: Engine
log = get_logger()


def create(conf: Config):
    global engine

    if conf.DB_ENGINE == DB_ENGINE_POSTGRES:
        log.info(f"Database url: {conf.get_postgres_url()}")
        engine = create_engine(conf.get_postgres_url(), echo=True)
    elif conf.DB_ENGINE == DB_ENGINE_SQLITE:
        log.info(f"Database url: {conf.get_sqlite_url()}")
        engine = create_engine(conf.get_sqlite_url(), echo=True)
    else:
        log.error(f"Invalid database engine specified ({conf.DB_ENGINE})")
        raise ValueError(f"Invalid database engine specified ({conf.DB_ENGINE})")

    migrate()
    return engine


def new_session():
    if not Engine:
        raise Exception("database engine is not initialized")
    session = Session(engine)
    return session


def migrate():
    from .models import User, TariffPlan

    metadata: MetaData = declarative_base().metadata
    metadata.create_all(engine, tables=[User.__table__, TariffPlan.__table__])
