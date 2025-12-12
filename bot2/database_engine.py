from sqlalchemy import create_engine, Engine, MetaData
from sqlalchemy.orm import Session, declarative_base, DeclarativeBase
from .config import Config
from .logger import get_logger

engine: Engine
log = get_logger


def create(conf: Config):
    global engine
    engine = create_engine(conf.get_postgres_url(), echo=True)
    migrate()
    return engine


def new_session():
    if not Engine:
        raise Exception("database engine is not initialized")
    session = Session(engine)
    return session


def migrate():
    from .models import User, TariffPlan
    metadata :MetaData= declarative_base().metadata
    metadata.create_all(engine, tables=[User.__table__, TariffPlan.__table__])
