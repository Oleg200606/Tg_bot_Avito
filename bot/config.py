import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # Telegram
    BOT_TOKEN = os.getenv("BOT_TOKEN", "")
    ADMIN_IDS = (
        list(map(int, os.getenv("ADMIN_IDS", "").split(",")))
        if os.getenv("ADMIN_IDS")
        else []
    )

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

    # Bot username (auto-detected from token)
    BOT_USERNAME = os.getenv("BOT_USERNAME", "")

    # Admin panel
    ADMIN_PANEL_URL = os.getenv("ADMIN_PANEL_URL", "http://localhost:5000")

    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

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

    @classmethod
    def validate(cls):
        """Валидация конфигурации"""
        errors: list[str] = []

        if not cls.BOT_TOKEN:
            errors.append("BOT_TOKEN не установлен")

        if not cls.YOOKASSA_SHOP_ID:
            errors.append("YOOKASSA_SHOP_ID не установлен")

        if not cls.YOOKASSA_SECRET_KEY:
            errors.append("YOOKASSA_SECRET_KEY не установлен")

        if not cls.DB_PASSWORD:
            errors.append("DB_PASSWORD не установлен")

        # Автоматически определяем username бота из токена
        if cls.BOT_TOKEN and not cls.BOT_USERNAME:
            try:
                from aiogram import Bot
                import asyncio

                bot = Bot(token=cls.BOT_TOKEN)

                # Создаем новую event loop для синхронного вызова
                import nest_asyncio

                nest_asyncio.apply()

                bot_info = asyncio.run(bot.get_me())
                cls.BOT_USERNAME = bot_info.username
                print(f"✅ Автоопределен BOT_USERNAME: @{cls.BOT_USERNAME}")
            except Exception as e:
                print(f"⚠️ Не удалось определить username бота: {e}")
                cls.BOT_USERNAME = "avitoparser_rus_bot"

        if errors:
            raise ValueError(f"Ошибки конфигурации: {', '.join(errors)}")

    @classmethod
    def get_plan_by_key(cls, plan_key):
        """Получить план по ключу"""
        return cls.SUBSCRIPTION_PLANS.get(plan_key)

    @classmethod
    def get_all_plans(cls):
        """Получить все планы"""
        return cls.SUBSCRIPTION_PLANS

    @classmethod
    def format_price(cls, price):
        """Форматирование цены"""
        return f"{price}₽"

    @classmethod
    def get_subscription_plans_display(cls):
        """Получить отформатированный список планов для отображения"""
        plans_text = ""
        for key, plan in cls.SUBSCRIPTION_PLANS.items():
            plans_text += f"{key}. {plan['name']} - {cls.format_price(plan['price'])}\n"
        return plans_text
