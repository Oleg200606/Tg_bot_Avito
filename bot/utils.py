import re
from datetime import datetime
from urllib.parse import urlparse

def validate_url(url: str) -> bool:
    """Проверка валидности URL"""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

def format_date(date: datetime) -> str:
    """Форматирование даты"""
    return date.strftime("%d.%m.%Y %H:%M")

def format_time_left(end_date: datetime) -> str:
    """Форматирование оставшегося времени"""
    now = datetime.now()
    if end_date < now:
        return "Истекла"
    
    delta = end_date - now
    days = delta.days
    hours = delta.seconds // 3600
    minutes = (delta.seconds % 3600) // 60
    
    if days > 0:
        return f"{days} д. {hours} ч."
    elif hours > 0:
        return f"{hours} ч. {minutes} мин."
    else:
        return f"{minutes} мин."

def format_price(amount: float) -> str:
    """Форматирование цены"""
    return f"{int(amount)}₽"

def is_admin(telegram_id: int, admin_ids: list) -> bool:
    """Проверка, является ли пользователь админом"""
    return telegram_id in admin_ids