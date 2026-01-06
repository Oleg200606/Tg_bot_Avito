from .logger import get_logger
from .models import Target

log = get_logger(__name__)


def check_can_create_target(user_id: int) -> bool:
    """Must check user subscription and its limits"""
    log.warning("Check_can_create_target is not implemented")
    return True


def create_target(user_id: int, url: str) -> Target | None:
    if not check_can_create_target(user_id):
        log.warning(f"Can't create target for user {user_id}")
        return None
