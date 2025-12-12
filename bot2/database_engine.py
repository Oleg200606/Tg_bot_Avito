from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import Session
from .config import Config


engine: Engine


def create(conf: Config):
    global engine
    engine = create_engine(conf.get_postgres_url(), echo=True)
    return engine

def new_session():
    if not Engine:
        raise Exception("database engine is not initialized")
    session = Session(engine)
    return session
