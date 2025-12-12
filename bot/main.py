import asyncio
import logging
import sys
from datetime import datetime

from ..bot2.keyboards import get_main_menu, get_subscription_plans

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from config import Config
from .database import Database, db_instance
from payment_handler import YooKassaPayment
from utils import validate_url

# Настройка логирования для Docker
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# Инициализация бота
try:
    Config.validate()
    bot = Bot(
        token=Config.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()
except Exception as e:
    logger.error(f"Ошибка инициализации бота: {e}")
    sys.exit(1)


# Функция для ожидания готовности БД
async def wait_for_db(retries: int = 10, delay: int = 5):
    global db_instance
    """Ожидание подключения к БД"""
    for i in range(retries):
        try:
            db_instance = await Database.create()
            logger.info(f"Попытка подключения к БД {i+1}/{retries}")
            await db_instance.create_tables()
            logger.info("✅ Подключение к БД установлено")
            return True
        except Exception as e:
            logger.warning(f"Ошибка подключения к БД: {e}")
            if i < retries - 1:
                logger.info(f"Повторная попытка через {delay} секунд...")
                await asyncio.sleep(delay)
            else:
                logger.error("Не удалось подключиться к БД после всех попыток")
                return False


# Команда /start
@dp.message(Command("start"))
async def cmd_start(message: Message):
    try:
        user = await db_instance.get_or_create_user(
            telegram_id=message.from_user.id,
            username=message.from_user.username ,
            full_name=message.from_user.full_name or "Пользователь",
        )

        if not user:
            await message.answer(
                "❌ Ошибка при создании пользователя. Попробуйте позже."
            )
            return

        is_admin = message.from_user.id in Config.ADMIN_IDS

        welcome_text = f"""👋 Привет, {message.from_user.first_name}!

🤖 Я бот для управления подписками с Яндекс Кассой.

✨ <b>Доступные функции:</b>
• Безопасная оплата через Яндекс Кассу
• Добавление ссылок с учетом лимита
• Просмотр статистики и истории
• Автоматическое обновление подписок

💎 <b>Тарифные планы:</b>
1. 1 месяц (5 запросов) - 500₽
2. 3 месяца (15 запросов) - 1200₽
3. 6 месяцев (30 запросов) - 2000₽
4. 12 месяцев (60 запросов) - 3500₽

<b>Запрос</b> - добавление одной ссылки. Лимит обновляется при продлении.

Используйте кнопки ниже для навигации! 🚀"""

        await message.answer(welcome_text, reply_markup=get_main_menu(is_admin))

    except Exception as e:
        logger.error(f"Ошибка в /start: {e}")
        await message.answer("Привет! Используйте команды из меню.")


# Обработка покупки подписки
@dp.message(F.text == "💎 Купить подписку")
async def buy_subscription(message: Message):
    text = """💎 <b>Выберите тарифный план:</b>

1. <b>1 месяц</b> - 500₽
   • 5 запросов ссылок
   • Доступ на 30 дней

2. <b>3 месяца</b> - 1200₽ (экономия 20%)
   • 15 запросов ссылок
   • Доступ на 90 дней

3. <b>6 месяцев</b> - 2000₽ (экономия 33%)
   • 30 запросов ссылок
   • Доступ на 180 дней

4. <b>12 месяцев</b> - 3500₽ (экономия 41%)
   • 60 запросов ссылок
   • Доступ на 365 дней

Выберите подходящий вариант:"""

    await message.answer(text, reply_markup=get_subscription_plans())


# Обработка выбора тарифа
@dp.callback_query(F.data.startswith("buy_"))
async def process_buy_callback(callback: CallbackQuery):
    plan_key = callback.data.split("_")[1]

    if plan_key not in Config.SUBSCRIPTION_PLANS:
        await callback.answer("❌ Тарифный план не найден")
        return

    plan = Config.SUBSCRIPTION_PLANS[plan_key]

    # Получаем пользователя
    user = await db_instance.get_or_create_user(
        telegram_id=callback.from_user.id,
        username=callback.from_user.username,
        full_name=callback.from_user.full_name or "Пользователь",
    )

    if not user:
        await callback.answer("❌ Ошибка пользователя")
        return

    await callback.answer("⏳ Создаем платеж...")

    # Создаем платеж
    payment_result = await YooKassaPayment.create_payment(
        user_id=user["id"], plan_key=plan_key, telegram_id=callback.from_user.id
    )

    if payment_result["success"]:
        payment_text = f"""✅ <b>Платеж создан!</b>

💳 <b>Сумма:</b> {payment_result['amount']}₽
📋 <b>Тариф:</b> {payment_result['plan_name']}
📅 <b>Доступно запросов:</b> {plan['requests']}

<b>Для оплаты перейдите по ссылке:</b>
{payment_result['confirmation_url']}

⚠️ <b>Важно:</b>
• После успешной оплаты подписка активируется автоматически
• Обычно это занимает 1-2 минуты
• Проверить статус можно в "📊 Моя статистика"

<b>В случае проблем:</b>
• Если оплата прошла, но подписка не активировалась
• Или возникли другие вопросы
• Обратитесь в поддержку"""

        await callback.message.answer(payment_text)
    else:
        error_msg = payment_result.get("error", "Неизвестная ошибка")
        logger.error(f"Ошибка создания платежа: {error_msg}")
        await callback.message.answer(
            f"❌ Ошибка создания платежа: {error_msg}\n\nПопробуйте позже или обратитесь в поддержку."
        )

    await callback.answer()


# Добавление ссылки с проверкой лимита
@dp.message(F.text == "🔗 Добавить ссылку")
async def add_link_command(message: Message):
    user = await db_instance.get_or_create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        full_name=message.from_user.full_name or "Пользователь",
    )

    if not user:
        await message.answer("❌ Ошибка пользователя")
        return

    # Проверяем лимит запросов
    limit_check = await db_instance.check_request_limit(user["id"])

    if not limit_check["has_access"]:
        await message.answer(limit_check["message"])
        return

    await message.answer(
        f"✅ <b>Доступно:</b> {limit_check['remaining']} из {limit_check['total']} запросов\n\n"
        f"Отправьте мне ссылку для сохранения (формат: https://example.com):"
    )


# Обработка ссылок
@dp.message(F.text.contains("http"))
async def handle_link_message(message: Message):
    # Валидация URL
    if not validate_url(message.text):
        await message.answer(
            "❌ Некорректная ссылка. Используйте формат: https://example.com"
        )
        return

    user = await db_instance.get_or_create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        full_name=message.from_user.full_name or "Пользователь",
    )

    if not user:
        await message.answer("❌ Ошибка пользователя")
        return

    # Проверяем лимит запросов
    limit_check = await db_instance.check_request_limit(user["id"])

    if not limit_check["has_access"]:
        await message.answer(limit_check["message"])
        return

    try:
        # Добавляем ссылку
        await db_instance.add_user_link(user["id"], message.text)

        # Увеличиваем счетчик запросов
        await db_instance.increment_request_count(
            user["id"], limit_check["subscription_id"], message.text
        )

        # Обновляем информацию о лимите
        new_limit = await db_instance.check_request_limit(user["id"])

        await message.answer(
            f"✅ <b>Ссылка сохранена!</b>\n\n"
            f"🔗 {message.text[:50]}...\n\n"
            f"📊 <b>Осталось запросов:</b> {new_limit['remaining']}/{new_limit['total']}"
        )
    except Exception as e:
        logger.error(f"Ошибка сохранения ссылки: {e}")
        await message.answer("❌ Ошибка при сохранении ссылки. Попробуйте позже.")


# Статистика пользователя
@dp.message(F.text == "📊 Моя статистика")
async def user_statistics(message: Message):
    user = await db_instance.get_or_create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        full_name=message.from_user.full_name or "Пользователь",
    )

    if not user:
        await message.answer("❌ Ошибка пользователя")
        return

    stats = await db_instance.get_user_statistics(user["id"])

    if stats.get("plan"):
        end_date = (
            stats["end_date"].strftime("%d.%m.%Y") if stats["end_date"] else "Нет"
        )
        days_left = (
            (stats["end_date"].date() - datetime.now().date()).days
            if stats["end_date"]
            else 0
        )
        days_left_text = f"{days_left} дн." if days_left > 0 else "<b>Истекла</b>"

        text = f"""📊 <b>Ваша статистика</b>

👤 <b>Пользователь:</b> {stats['full_name'] or 'Не указано'}
📅 <b>Регистрация:</b> {stats['created_at'].strftime('%d.%m.%Y')}

💎 <b>Подписка:</b>
• Тариф: {stats['plan']}
• Действует до: {end_date}
• Осталось дней: {days_left_text}
• Лимит запросов: {stats['used_requests']}/{stats['request_limit']}

📈 <b>Активность:</b>
• Всего запросов: {stats['total_requests'] or 0}
• Всего платежей: {stats['total_payments'] or 0}
• Потрачено: {stats['total_spent'] or 0}₽

💡 <b>Совет:</b> Следите за лимитом запросов и продлевайте подписку вовремя!"""
    else:
        text = """📊 <b>Ваша статистика</b>

❌ <b>У вас нет активной подписки.</b>

💎 Для доступа к функциям бота приобретите подписку:
• 1 месяц (5 запросов) - 500₽
• 3 месяца (15 запросов) - 1200₽
• 6 месяцев (30 запросов) - 2000₽
• 12 месяцев (60 запросов) - 3500₽

<b>Нажмите "💎 Купить подписку" для выбора тарифа.</b>

✨ <b>Что дает подписка:</b>
• Возможность добавлять ссылки
• Доступ ко всем функциям бота
• Приоритетную поддержку
• Автоматическое обновление"""

    await message.answer(text)


# Инструкции
@dp.message(F.text == "📋 Инструкция")
async def show_instructions(message: Message):
    try:
        instructions = await db_instance.get_instructions()

        if instructions:
            text = "📖 <b>Инструкции по использованию бота:</b>\n\n"
            for inst in instructions:
                text += f"<b>{inst['title']}</b>\n{inst['text_content']}\n\n"
        else:
            text = "📝 Инструкции будут добавлены позже."

        await message.answer(text)
    except Exception as e:
        logger.error(f"Ошибка загрузки инструкций: {e}")
        await message.answer("❌ Ошибка загрузки инструкций. Попробуйте позже.")


# Админ панель
@dp.message(F.text == "👑 Админ панель")
async def admin_panel(message: Message):
    if message.from_user.id not in Config.ADMIN_IDS:
        await message.answer("⛔ Доступ запрещен")
        return

    text = f"""👑 <b>Админ панель</b>

Для полного управления системой используйте веб-панель:
{Config.ADMIN_PANEL_URL}

<b>Основные функции веб-панели:</b>
• Управление пользователями и подписками
• Настройка тарифных планов
• Просмотр статистики и платежей
• Редактирование инструкций
• Мониторинг системы

<b>Базовые команды в боте:</b>
• /stats - Статистика бота
• /users - Список пользователей
• /payments - Статистика платежей"""

    await message.answer(text)


# Команды для админов
@dp.message(Command("stats"))
async def admin_stats(message: Message):
    if message.from_user.id not in Config.ADMIN_IDS:
        return

    try:
        stats = await db_instance.get_statistics()
        payment_stats = await db_instance.get_payments_statistics(30)

        text = f"""📊 <b>Статистика бота</b>

👥 <b>Пользователей:</b> {stats.get('total_users', 0)}
💎 <b>Активных подписок:</b> {stats.get('current_subscribers', 0)}
🔗 <b>Всего ссылок:</b> {stats.get('total_links', 0)}

💰 <b>Финансы (за 30 дней):</b>
• Всего платежей: {payment_stats.get('total_payments', 0)}
• Успешных: {payment_stats.get('successful_payments', 0)}
• В ожидании: {payment_stats.get('pending_payments', 0)}
• Выручка: {payment_stats.get('total_revenue', 0)}₽
• Средний чек: {payment_stats.get('avg_payment', 0):.2f}₽

📈 <b>Использование лимитов:</b>
• Использовано запросов: {stats.get('total_requests_used', 0)}
• Всего доступно: {stats.get('total_requests_limit', 0)}"""

        await message.answer(text)
    except Exception as e:
        logger.error(f"Ошибка статистики: {e}")
        await message.answer("❌ Ошибка загрузки статистики")


# Кнопка "Назад"
@dp.callback_query(F.data == "back_to_main")
async def back_to_main(callback: CallbackQuery):
    user = await db_instance.get_or_create_user(
        telegram_id=callback.from_user.id,
        username=callback.from_user.username,
        full_name=callback.from_user.full_name or "Пользователь",
    )

    if user:
        is_admin = callback.from_user.id in Config.ADMIN_IDS
        await callback.message.edit_text("Главное меню", reply_markup=None)
        await callback.message.answer(
            "Главное меню", reply_markup=get_main_menu(is_admin)
        )

    await callback.answer()


@dp.message(Command("users"))
async def admin_users(message: Message):
    if message.from_user.id not in Config.ADMIN_IDS:
        return

    try:
        users = await db_instance.get_all_users(20)

        if not users:
            await message.answer("📭 Пользователей нет")
            return

        text = "👥 <b>Последние 20 пользователей:</b>\n\n"
        for user in users:
            created_at = user["created_at"].strftime("%d.%m.%Y %H:%M")
            text += f"👤 <b>{user['full_name'] or 'Без имени'}</b>\n"
            text += f"   ID: {user['telegram_id']}\n"
            text += f"   @{user['username'] or 'нет'}\n"
            text += f"   📅 Регистрация: {created_at}\n"
            text += f"   💎 Подписок: {user['total_subscriptions']}\n"
            text += f"   💳 Платежей: {user['total_payments']}\n"

            if user["last_subscription_end"]:
                last_sub = user["last_subscription_end"].strftime("%d.%m.%Y")
                text += f"   📅 Последняя подписка до: {last_sub}\n"

            text += "─" * 30 + "\n"

        await message.answer(text)
    except Exception as e:
        logger.error(f"Ошибка загрузки пользователей: {e}")
        await message.answer("❌ Ошибка загрузки пользователей")


# Основная функция
async def main():
    logger.info("🚀 Запуск бота подписки...")

    # Ждем подключения к БД
    if not await wait_for_db():
        logger.error("Не удалось подключиться к БД. Завершение работы.")
        sys.exit(1)

    # Запуск бота
    try:
        logger.info("✅ Бот запущен и готов к работе!")
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Ошибка запуска бота: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
