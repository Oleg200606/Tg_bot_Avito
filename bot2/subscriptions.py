from .models import Subscription
from .logger import get_logger

log = get_logger(__name__)


def get_subscription(user_id: int) -> Subscription | None:
    return Subscription()


def _delete_overlimited_targets(): ...


def can_renew_subscription() -> bool:
    return True


def renew_subscription():
    """Interface"""
    if not can_renew_subscription():
        log.warning("Can't renew subscription")
        return

    _delete_overlimited_targets()
