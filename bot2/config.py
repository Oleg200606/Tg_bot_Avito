import os
from dotenv import load_dotenv

if not load_dotenv():
    raise Exception("Failed load .env file")


class Config:
    # Telegram
    BOT_TOKEN = os.getenv("BOT_TOKEN", "")

    ADMIN_IDS = (
        list(map(int, os.getenv("ADMIN_IDS", "").split(",")))
        if os.getenv("ADMIN_IDS")
        else []
    )
    # Bot username (auto-detected from token)
    BOT_USERNAME = os.getenv("BOT_USERNAME", "")

    # Database
    DB_HOST = os.getenv("DB_HOST", "postgres")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_NAME = os.getenv("DB_NAME", "avito_bot")
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")

    # YooKassa
    YOOKASSA_SHOP_ID = os.getenv("YOOKASSA_SHOP_ID", "")
    YOOKASSA_SECRET_KEY = os.getenv("YOOKASSA_SECRET_KEY", "")
    YOOKASSA_RETURN_URL = os.getenv(
        "YOOKASSA_RETURN_URL", "https://t.me/avitoparser_rus_bot"
    )

    # Settings for receipts (54-ФЗ)
    DEFAULT_EMAIL = os.getenv("DEFAULT_EMAIL", "user@example.com")
    VAT_CODE = os.getenv("VAT_CODE", "4")  # 4 = без НДС (для УСН)
    TAX_SYSTEM_CODE = os.getenv("TAX_SYSTEM_CODE", "2")  # 2 = УСН доходы

    # Admin panel
    ADMIN_PANEL_URL = os.getenv("ADMIN_PANEL_URL", "http://localhost:5000")

    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    def __init__(self) -> None:
        if not self.BOT_TOKEN:
            raise ValueError("BOT_TOKEN не установлен")
        if not self.DB_PASSWORD:
            raise ValueError("DB_PASSWORD не установлен")
    def get_postgres_url(self):
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    # VAT codes explanation:
    # 1 = НДС 20%
    # 2 = НДС 10%
    # 3 = НДС 0%
    # 4 = без НДС (используется для УСН)
    # 5 = НДС 20/120%
    # 6 = НДС 10/110%

    # Tax system codes explanation:
    # 1 = Общая система налогообложения (ОСН)
    # 2 = Упрощенная система налогообложения (УСН) доходы
    # 3 = Упрощенная система налогообложения (УСН) доходы минус расходы
    # 4 = Единый налог на вмененный доход (ЕНВД)
    # 5 = Единый сельскохозяйственный налог (ЕСХН)
    # 6 = Патентная система налогообложения


def format_price(price: str):
    """Форматирование цены"""
    return f"{price}₽"
