from .models import User
from sqlalchemy import select
from .database_engine import new_session
from .logger import get_logger


log = get_logger(__name__)

def get_user_by_telegram_id(telegram_id: int) -> User | None:

    with new_session() as session:
        statement =select(User).where(User.telegram_id == telegram_id)
        user = session.scalar(statement)
        if not User:
            log.error("No such user with telegram id %d", telegram_id)
            return None
        return user

def create_user(telegram_id: int, username: str) -> User |None:
    user = User()
    user.username = username
    user.telegram_id = telegram_id
    with new_session() as session:
        try:
            session.add(user)
            session.commit()
        except Exception as e:
            log.error("Failed create user. Error: %s", e)
            return None

    return user
    
def get_or_create_user(
        telegram_id: int,
        username: str,
) -> User:
    usr = get_user_by_telegram_id(telegram_id)
    if not usr:
        new_user = create_user(telegram_id=telegram_id, username=username)
        if not new_user:
            raise Exception("failed create new user", telegram_id, username)
        return new_user
    else:
        return usr
