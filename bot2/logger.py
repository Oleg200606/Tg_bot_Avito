import sys
import logging
from .config import Config

def setup(conf: Config):
    global log

    logging.basicConfig(
        level=getattr(logging, conf.LOG_LEVEL),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

def get_logger(name: str | None = None) -> logging.Logger:
    return logging.getLogger(name)
