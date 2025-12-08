import asyncio
import logging
import os
import sys
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, Router, F
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
import asyncpg

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Конфигурация
BOT_TOKEN = os.getenv("BOT_TOKEN", "8288743182:AAHif2v8dN0M0BGN7PCACfmJlekAR_d-hE0")
ADMIN_IDS = [1226131544, 936840809]

# Database
DB_CONFIG = {
    'host': os.getenv("DB_HOST", "postgres"),
    'port': os.getenv("DB_PORT", "5432"),
    'database': os.getenv("DB_NAME", "avito_bot"),
    'user': os.getenv("DB_USER", "postgres"),
    'password': os.getenv("DB_PASSWORD", "1")
}

# Исправленная инициализация бота для aiogram 3.10.0
bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()

class Database:
    def __init__(self):
        self.pool = None
    
    async def connect(self):
        try:
            self.pool = await asyncpg.create_pool(**DB_CONFIG)
            logger.info("✅ Подключение к БД установлено")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка подключения к БД: {e}")
            return False
    
    async def init_tables(self):
        async with self.pool.acquire() as conn:
            # Создаем таблицы если их нет
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    telegram_id BIGINT UNIQUE NOT NULL,
                    username VARCHAR(255),
                    full_name VARCHAR(255),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_admin BOOLEAN DEFAULT FALSE
                )
            ''')
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS subscriptions (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    start_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    end_date TIMESTAMP NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    payment_id VARCHAR(255),
                    plan VARCHAR(50) DEFAULT 'basic'
                )
            ''')
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS user_links (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    link TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS instructions (
                    id SERIAL PRIMARY KEY,
                    title VARCHAR(255) NOT NULL,
                    text_content TEXT,
                    video_url VARCHAR(500),
                    order_index INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            logger.info("✅ Таблицы проверены/созданы")
            
            # Добавляем тестовые инструкции
            count = await conn.fetchval('SELECT COUNT(*) FROM instructions')
            if count == 0:
                await conn.execute('''
                    INSERT INTO instructions (title, text_content, order_index) VALUES
                    ('Как пользоваться ботом', '1. Купите подписку\n2. Добавляйте ссылки\n3. Получайте доступ к функциям', 1),
                    ('Как добавить ссылку', 'Нажмите кнопку "🔗 Добавить ссылку" и отправьте ссылку', 2)
                ''')
                logger.info("✅ Добавлены тестовые инструкции")

db = Database()

@dp.message(Command("start"))
async def cmd_start(message: Message):
    """Обработчик команды /start"""
    try:
        async with db.pool.acquire() as conn:
            user = await conn.fetchrow(
                'SELECT * FROM users WHERE telegram_id = $1',
                message.from_user.id
            )
            
            if not user:
                is_admin = message.from_user.id in ADMIN_IDS
                user = await conn.fetchrow(
                    '''INSERT INTO users (telegram_id, username, full_name, is_admin)
                       VALUES ($1, $2, $3, $4) RETURNING *''',
                    message.from_user.id,
                    message.from_user.username,
                    message.from_user.full_name or "Пользователь",
                    is_admin
                )
                logger.info(f"✅ Создан пользователь: {message.from_user.id}")
        
        # Создаем клавиатуру
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📋 Инструкция"), KeyboardButton(text="💎 Подписка")],
                [KeyboardButton(text="🔗 Добавить ссылку"), KeyboardButton(text="📞 Помощь")],
                [KeyboardButton(text="📊 Статистика")]
            ],
            resize_keyboard=True
        )
        
        text = f"""👋 Привет, {message.from_user.full_name or 'друг'}!

🤖 Я бот для управления подписками.

✨ Функции:
• Покупка и управление подписками
• Хранение ссылок
• Инструкции и помощь
• Статистика

Нажмите кнопки ниже или напишите /help"""
        
        await message.answer(text, reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"Ошибка в /start: {e}")
        await message.answer("Привет! Я бот. Используйте команды из меню.")

@dp.message(F.text == "📋 Инструкция")
async def show_instructions(message: Message):
    try:
        async with db.pool.acquire() as conn:
            instructions = await conn.fetch('SELECT * FROM instructions ORDER BY order_index ASC')
        
        if instructions:
            text = "📖 <b>Инструкции по использованию бота:</b>\n\n"
            for inst in instructions:
                text += f"<b>{inst['title']}</b>\n{inst['text_content']}\n"
                if inst['video_url']:
                    text += f"Видео: {inst['video_url']}\n"
                text += "\n"
        else:
            text = "Инструкции пока не добавлены."
        
        await message.answer(text)
        
    except Exception as e:
        logger.error(f"Ошибка показа инструкций: {e}")
        await message.answer("Ошибка при загрузке инструкций.")

@dp.message(F.text == "💎 Подписка")
async def show_subscription(message: Message):
    try:
        async with db.pool.acquire() as conn:
            user = await conn.fetchrow(
                'SELECT * FROM users WHERE telegram_id = $1',
                message.from_user.id
            )
            
            if user:
                subscription = await conn.fetchrow(
                    '''SELECT * FROM subscriptions 
                       WHERE user_id = $1 AND is_active = TRUE 
                       AND end_date > CURRENT_TIMESTAMP''',
                    user['id']
                )
                
                if subscription:
                    end_date = subscription['end_date'].strftime("%d.%m.%Y")
                    days_left = (subscription['end_date'].date() - datetime.now().date()).days
                    text = f"""✅ <b>Ваша подписка активна</b>

📅 Действует до: {end_date}
⏰ Осталось дней: {days_left}
🎯 Тариф: {subscription['plan']}
"""
                else:
                    text = """❌ <b>У вас нет активной подписки</b>

💎 <b>Доступные тарифы:</b>
• 1 месяц - 500₽
• 3 месяца - 1200₽ (экономия 10%)
• 6 месяцев - 2000₽ (экономия 17%)
• 12 месяцев - 3500₽ (экономия 30%)

Для покупки напишите /buy"""
            else:
                text = "Сначала используйте /start"
        
        await message.answer(text)
        
    except Exception as e:
        logger.error(f"Ошибка подписки: {e}")
        await message.answer("Ошибка при проверке подписки")

@dp.message(F.text == "🔗 Добавить ссылку")
async def add_link(message: Message):
    try:
        async with db.pool.acquire() as conn:
            user = await conn.fetchrow(
                'SELECT * FROM users WHERE telegram_id = $1',
                message.from_user.id
            )
            
            if user:
                subscription = await conn.fetchrow(
                    '''SELECT * FROM subscriptions 
                       WHERE user_id = $1 AND is_active = TRUE 
                       AND end_date > CURRENT_TIMESTAMP''',
                    user['id']
                )
                
                if subscription:
                    await message.answer("🔗 Отправьте мне ссылку для сохранения (формат: https://example.com):")
                else:
                    await message.answer("❌ <b>Только для подписчиков!</b>\n\nКупите подписку через кнопку '💎 Подписка' или команду /buy")
            else:
                await message.answer("Сначала используйте /start")
                
    except Exception as e:
        logger.error(f"Ошибка добавления ссылки: {e}")
        await message.answer("Ошибка")

@dp.message(F.text == "📞 Помощь")
async def show_help(message: Message):
    text = """📞 <b>Помощь и поддержка</b>

<b>Основные команды:</b>
/start - Начать работу
/help - Эта справка
/buy - Купить подписку
/subscription - Проверить подписку
/link - Добавить ссылку

<b>Для администраторов:</b>
/admin - Панель админа
/users - Список пользователей
/stats - Статистика

<b>Проблемы?</b>
Обратитесь к администратору."""
    
    await message.answer(text)

@dp.message(F.text == "📊 Статистика")
async def show_stats(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("Эта функция доступна только администраторам.")
        return
    
    try:
        async with db.pool.acquire() as conn:
            users_count = await conn.fetchval('SELECT COUNT(*) FROM users')
            active_subs = await conn.fetchval('''
                SELECT COUNT(*) FROM subscriptions 
                WHERE is_active = TRUE AND end_date > CURRENT_TIMESTAMP
            ''')
            total_links = await conn.fetchval('SELECT COUNT(*) FROM user_links')
            
            # Добавляем тестовую подписку для админа
            admin_user = await conn.fetchrow('SELECT * FROM users WHERE telegram_id = $1', message.from_user.id)
            if admin_user:
                has_sub = await conn.fetchrow('SELECT * FROM subscriptions WHERE user_id = $1', admin_user['id'])
                if not has_sub:
                    end_date = datetime.now() + timedelta(days=365)
                    await conn.execute('''
                        INSERT INTO subscriptions (user_id, end_date, plan)
                        VALUES ($1, $2, $3)
                    ''', admin_user['id'], end_date, 'admin')
        
        text = f"""📊 <b>Статистика бота</b>

👥 Всего пользователей: {users_count}
✅ Активных подписок: {active_subs}
🔗 Сохранено ссылок: {total_links}
👑 Вы администратор"""
        
        await message.answer(text)
        
    except Exception as e:
        logger.error(f"Ошибка статистики: {e}")
        await message.answer("Ошибка при получении статистики.")

@dp.message(Command("buy"))
async def cmd_buy(message: Message):
    """Покупка подписки"""
    text = """💎 <b>Покупка подписки</b>

Выберите тариф:
1. 1 месяц - 500₽
2. 3 месяца - 1200₽
3. 6 месяцев - 2000₽
4. 12 месяцев - 3500₽

Для тестирования, администраторы получают бесплатную подписку автоматически.

<b>Оплата:</b>
Переведите средства на карту XXX XXX XXX
и отправьте скриншот оплаты администратору."""
    
    await message.answer(text)

@dp.message(Command("admin"))
async def cmd_admin(message: Message):
    """Панель администратора"""
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("⛔ У вас нет доступа к этой команде.")
        return
    
    try:
        async with db.pool.acquire() as conn:
            users_count = await conn.fetchval('SELECT COUNT(*) FROM users')
            subs_count = await conn.fetchval('''
                SELECT COUNT(DISTINCT user_id) 
                FROM subscriptions 
                WHERE is_active = TRUE AND end_date > CURRENT_TIMESTAMP
            ''')
            recent_users = await conn.fetch('SELECT * FROM users ORDER BY created_at DESC LIMIT 5')
        
        recent_text = ""
        for user in recent_users:
            date = user['created_at'].strftime("%d.%m")
            recent_text += f"• {user['full_name'] or 'Без имени'} ({date})\n"
        
        text = f"""👑 <b>Панель администратора</b>

📊 <b>Статистика:</b>
• Пользователей: {users_count}
• Активных подписок: {subs_count}

👥 <b>Последние пользователи:</b>
{recent_text}

<b>Команды админа:</b>
• /users - Полный список
• /stats - Детальная статистика
• Добавить ссылку вручную: /addlink [user_id] [ссылка]"""
        
        await message.answer(text)
        
    except Exception as e:
        logger.error(f"Ошибка в /admin: {e}")
        await message.answer("Ошибка при получении статистики.")

@dp.message(Command("users"))
async def cmd_users(message: Message):
    """Список пользователей (админ)"""
    if message.from_user.id not in ADMIN_IDS:
        return
    
    try:
        async with db.pool.acquire() as conn:
            users = await conn.fetch('SELECT * FROM users ORDER BY created_at DESC LIMIT 15')
        
        if not users:
            await message.answer("Нет пользователей.")
            return
        
        text = "👥 <b>Последние 15 пользователей:</b>\n\n"
        for user in users:
            created = user['created_at'].strftime("%d.%m")
            admin = "👑" if user['is_admin'] else "👤"
            text += f"{admin} <b>{user['full_name'] or 'Без имени'}</b>\n"
            text += f"   @{user['username'] or 'нет'}\n"
            text += f"   ID: {user['telegram_id']}, Дата: {created}\n\n"
        
        await message.answer(text)
        
    except Exception as e:
        logger.error(f"Ошибка в /users: {e}")
        await message.answer("Ошибка при получении списка пользователей.")

@dp.message(Command("test"))
async def cmd_test(message: Message):
    """Тестовая команда"""
    await message.answer(f"✅ <b>Бот работает!</b>\n\nВаш ID: <code>{message.from_user.id}</code>\nИмя: {message.from_user.full_name}")

@dp.message(Command("db"))
async def cmd_db(message: Message):
    """Проверка БД"""
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("Только для админов")
        return
    
    try:
        async with db.pool.acquire() as conn:
            users_count = await conn.fetchval('SELECT COUNT(*) FROM users')
            subs_count = await conn.fetchval('SELECT COUNT(*) FROM subscriptions')
            links_count = await conn.fetchval('SELECT COUNT(*) FROM user_links')
            instructions_count = await conn.fetchval('SELECT COUNT(*) FROM instructions')
            
            text = f"""✅ <b>База данных работает!</b>

📊 <b>Статистика БД:</b>
• Пользователей: {users_count}
• Подписок: {subs_count}
• Ссылок: {links_count}
• Инструкций: {instructions_count}

🎯 <b>Ваш статус:</b> Администратор"""
        
        await message.answer(text)
    except Exception as e:
        await message.answer(f"❌ <b>Ошибка БД:</b>\n<code>{str(e)}</code>")

@dp.message(F.text.contains("http"))
async def handle_link(message: Message):
    """Обработка ссылок от пользователей"""
    try:
        async with db.pool.acquire() as conn:
            user = await conn.fetchrow(
                'SELECT * FROM users WHERE telegram_id = $1',
                message.from_user.id
            )
            
            if user:
                subscription = await conn.fetchrow(
                    '''SELECT * FROM subscriptions 
                       WHERE user_id = $1 AND is_active = TRUE 
                       AND end_date > CURRENT_TIMESTAMP''',
                    user['id']
                )
                
                if subscription:
                    # Сохраняем ссылку
                    await conn.execute(
                        'INSERT INTO user_links (user_id, link) VALUES ($1, $2)',
                        user['id'], message.text
                    )
                    
                    # Получаем количество ссылок пользователя
                    links_count = await conn.fetchval(
                        'SELECT COUNT(*) FROM user_links WHERE user_id = $1',
                        user['id']
                    )
                    
                    text = f"""✅ <b>Ссылка сохранена!</b>

🔗 <code>{message.text[:50]}...</code>

📁 Всего ваших ссылок: {links_count}

Можете отправить следующую ссылку."""
                    
                    await message.answer(text)
                else:
                    await message.answer("❌ Только для подписчиков! Купите подписку через /buy")
            else:
                await message.answer("Сначала используйте /start")
                
    except Exception as e:
        logger.error(f"Ошибка сохранения ссылки: {e}")
        await message.answer("❌ Ошибка при сохранении ссылки. Убедитесь, что это корректная ссылка.")

async def main():
    logger.info("🚀 Запуск бота...")
    
    # Подключение к БД
    if not await db.connect():
        logger.error("Не удалось подключиться к БД")
        sys.exit(1)
    
    # Инициализация таблиц
    await db.init_tables()
    
    # Запуск бота
    logger.info("✅ Бот запущен и готов к работе!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())