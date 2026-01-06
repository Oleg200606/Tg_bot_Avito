from .logger import get_logger
from .models import Target
from .database_engine import new_session
from sqlalchemy import select

log = get_logger(__name__)


def can_create_target(user_id: int) -> bool:
    """Must check user subscription and its limits"""
    log.warning("Check_can_create_target is not implemented")
    return True


def create_target(user_id: int, url: str) -> Target | None:
    if not can_create_target(user_id):
        log.warning(f"Can't create target for user {user_id}")
        return None
    target = Target(user_id=user_id, url=url)
    with new_session() as session:
        session.add(target)
        session.commit()
        return target


def get_targets(user_id: int) -> list[Target]:
    statement = select(Target).where(Target.user_id == user_id)
    with new_session() as session:
        return list(session.scalars(statement))
