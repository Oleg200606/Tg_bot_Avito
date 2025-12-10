import os
import asyncpg
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from config import Config
import logging

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
    
    async def connect(self):
        """Подключение к базе данных"""
        try:
            self.pool = await asyncpg.create_pool(
                user=Config.DB_USER,
                password=Config.DB_PASSWORD,
                database=Config.DB_NAME,
                host=Config.DB_HOST,
                port=Config.DB_PORT
            )
            logger.info("✅ Подключение к БД успешно установлено")
        except Exception as e:
            logger.error(f"❌ Ошибка подключения к БД: {e}")
            raise
    
    async def create_tables(self):
        """Создание таблиц"""
        try:
            async with self.pool.acquire() as conn:
                # Таблица пользователей
                await conn.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        id SERIAL PRIMARY KEY,
                        telegram_id BIGINT UNIQUE NOT NULL,
                        username VARCHAR(255),
                        full_name VARCHAR(255),
                        created_at TIMESTAMP DEFAULT NOW()
                    )
                ''')
                
                # Таблица подписок
                await conn.execute('''
                    CREATE TABLE IF NOT EXISTS subscriptions (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                        plan_key VARCHAR(50) NOT NULL,
                        request_limit INTEGER NOT NULL,
                        used_requests INTEGER DEFAULT 0,
                        start_date TIMESTAMP DEFAULT NOW(),
                        end_date TIMESTAMP,
                        is_active BOOLEAN DEFAULT TRUE,
                        created_at TIMESTAMP DEFAULT NOW()
                    )
                ''')
                
                # Таблица платежей
                await conn.execute('''
                    CREATE TABLE IF NOT EXISTS payments (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                        subscription_id INTEGER REFERENCES subscriptions(id) ON DELETE SET NULL,
                        payment_id VARCHAR(255) UNIQUE NOT NULL,
                        amount DECIMAL(10, 2) NOT NULL,
                        plan_key VARCHAR(50) NOT NULL,
                        status VARCHAR(50) DEFAULT 'pending',
                        created_at TIMESTAMP DEFAULT NOW(),
                        updated_at TIMESTAMP DEFAULT NOW()
                    )
                ''')
                
                # Таблица ссылок
                await conn.execute('''
                    CREATE TABLE IF NOT EXISTS user_links (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                        subscription_id INTEGER REFERENCES subscriptions(id) ON DELETE SET NULL,
                        url TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT NOW()
                    )
                ''')
                
                # Таблица инструкций
                await conn.execute('''
                    CREATE TABLE IF NOT EXISTS instructions (
                        id SERIAL PRIMARY KEY,
                        title VARCHAR(255) NOT NULL,
                        text_content TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT NOW()
                    )
                ''')
                
                logger.info("✅ Таблицы созданы/проверены")
                
                # Добавляем инструкции по умолчанию
                await self.add_default_instructions()
        except Exception as e:
            logger.error(f"❌ Ошибка создания таблиц: {e}")
            raise
    
    async def get_or_create_user(self, telegram_id: int, username: str = None, full_name: str = None):
        """Получить или создать пользователя"""
        try:
            async with self.pool.acquire() as conn:
                # Пытаемся найти пользователя
                user = await conn.fetchrow(
                    'SELECT * FROM users WHERE telegram_id = $1',
                    telegram_id
                )
                
                if user:
                    # Обновляем информацию, если она изменилась
                    if username or full_name:
                        await conn.execute(
                            '''
                            UPDATE users 
                            SET username = COALESCE($2, username),
                                full_name = COALESCE($3, full_name)
                            WHERE id = $1
                            ''',
                            user['id'], username, full_name
                        )
                    return dict(user)
                else:
                    # Создаем нового пользователя
                    new_user = await conn.fetchrow(
                        '''
                        INSERT INTO users (telegram_id, username, full_name)
                        VALUES ($1, $2, $3)
                        RETURNING *
                        ''',
                        telegram_id, username, full_name
                    )
                    return dict(new_user)
        except Exception as e:
            logger.error(f"Ошибка get_or_create_user: {e}")
            return None
    
    async def get_user_statistics(self, user_id: int):
        """Получить статистику пользователя"""
        try:
            async with self.pool.acquire() as conn:
                # Получаем пользователя
                user = await conn.fetchrow(
                    'SELECT * FROM users WHERE id = $1',
                    user_id
                )
                
                if not user:
                    return {}
                
                # Получаем активную подписку
                subscription = await conn.fetchrow(
                    '''
                    SELECT * FROM subscriptions 
                    WHERE user_id = $1 AND is_active = TRUE 
                    ORDER BY end_date DESC LIMIT 1
                    ''',
                    user_id
                )
                
                # Получаем общую статистику
                stats = await conn.fetchrow(
                    '''
                    SELECT 
                        COUNT(DISTINCT ul.id) as total_requests,
                        COUNT(DISTINCT p.id) as total_payments,
                        COALESCE(SUM(p.amount) FILTER (WHERE p.status = 'succeeded'), 0) as total_spent
                    FROM users u
                    LEFT JOIN user_links ul ON u.id = ul.user_id
                    LEFT JOIN payments p ON u.id = p.user_id
                    WHERE u.id = $1
                    ''',
                    user_id
                )
                
                result = {
                    'full_name': user['full_name'],
                    'created_at': user['created_at'],
                    'plan': None,
                    'end_date': None,
                    'used_requests': 0,
                    'request_limit': 0,
                    'total_requests': stats['total_requests'] or 0,
                    'total_payments': stats['total_payments'] or 0,
                    'total_spent': float(stats['total_spent'] or 0)
                }
                
                if subscription:
                    plan = Config.SUBSCRIPTION_PLANS.get(subscription['plan_key'], {})
                    result.update({
                        'plan': plan.get('name', subscription['plan_key']),
                        'end_date': subscription['end_date'],
                        'used_requests': subscription['used_requests'],
                        'request_limit': subscription['request_limit']
                    })
                
                return result
        except Exception as e:
            logger.error(f"Ошибка get_user_statistics: {e}")
            return {}
    
    async def check_request_limit(self, user_id: int):
        """Проверить лимит запросов пользователя"""
        try:
            async with self.pool.acquire() as conn:
                # Получаем активную подписку
                subscription = await conn.fetchrow(
                    '''
                    SELECT * FROM subscriptions 
                    WHERE user_id = $1 AND is_active = TRUE 
                    AND (end_date IS NULL OR end_date > NOW())
                    ORDER BY end_date DESC LIMIT 1
                    ''',
                    user_id
                )
                
                if not subscription:
                    return {
                        'has_access': False,
                        'message': "❌ У вас нет активной подписки. Нажмите '💎 Купить подписку' для приобретения доступа.",
                        'remaining': 0,
                        'total': 0,
                        'subscription_id': None
                    }
                
                remaining = subscription['request_limit'] - subscription['used_requests']
                
                if remaining <= 0:
                    return {
                        'has_access': False,
                        'message': f"❌ Вы исчерпали лимит запросов ({subscription['used_requests']}/{subscription['request_limit']}). Лимит обновится при продлении подписки.",
                        'remaining': remaining,
                        'total': subscription['request_limit'],
                        'subscription_id': subscription['id']
                    }
                
                return {
                    'has_access': True,
                    'message': "",
                    'remaining': remaining,
                    'total': subscription['request_limit'],
                    'subscription_id': subscription['id']
                }
        except Exception as e:
            logger.error(f"Ошибка check_request_limit: {e}")
            return {
                'has_access': False,
                'message': "❌ Ошибка проверки лимита. Попробуйте позже.",
                'remaining': 0,
                'total': 0,
                'subscription_id': None
            }
    
    async def add_user_link(self, user_id: int, url: str):
        """Добавить ссылку пользователя"""
        try:
            async with self.pool.acquire() as conn:
                # Получаем активную подписку
                subscription = await conn.fetchrow(
                    '''
                    SELECT * FROM subscriptions 
                    WHERE user_id = $1 AND is_active = TRUE 
                    AND (end_date IS NULL OR end_date > NOW())
                    ORDER BY end_date DESC LIMIT 1
                    ''',
                    user_id
                )
                
                if subscription:
                    await conn.execute(
                        '''
                        INSERT INTO user_links (user_id, subscription_id, url)
                        VALUES ($1, $2, $3)
                        ''',
                        user_id, subscription['id'], url
                    )
                    return True
                return False
        except Exception as e:
            logger.error(f"Ошибка add_user_link: {e}")
            return False
    
    async def increment_request_count(self, user_id: int, subscription_id: int, url: str):
        """Увеличить счетчик запросов"""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute(
                    '''
                    UPDATE subscriptions 
                    SET used_requests = used_requests + 1
                    WHERE id = $1 AND user_id = $2
                    ''',
                    subscription_id, user_id
                )
                
                # Также добавляем ссылку
                await self.add_user_link(user_id, url)
                return True
        except Exception as e:
            logger.error(f"Ошибка increment_request_count: {e}")
            return False
    
    async def get_instructions(self):
        """Получить инструкции"""
        try:
            async with self.pool.acquire() as conn:
                instructions = await conn.fetch(
                    'SELECT * FROM instructions ORDER BY created_at DESC'
                )
                return [dict(inst) for inst in instructions]
        except Exception as e:
            logger.error(f"Ошибка get_instructions: {e}")
            return []
    
    async def get_statistics(self):
        """Получить общую статистику"""
        try:
            async with self.pool.acquire() as conn:
                stats = await conn.fetchrow('''
                    SELECT 
                        COUNT(DISTINCT u.id) as total_users,
                        COUNT(DISTINCT s.id) FILTER (WHERE s.is_active = TRUE AND (s.end_date IS NULL OR s.end_date > NOW())) as current_subscribers,
                        COUNT(DISTINCT ul.id) as total_links,
                        COALESCE(SUM(s.used_requests), 0) as total_requests_used,
                        COALESCE(SUM(s.request_limit), 0) as total_requests_limit
                    FROM users u
                    LEFT JOIN subscriptions s ON u.id = s.user_id
                    LEFT JOIN user_links ul ON u.id = ul.user_id
                ''')
                return dict(stats) if stats else {}
        except Exception as e:
            logger.error(f"Ошибка get_statistics: {e}")
            return {}
    
    async def get_payments_statistics(self, days: int = 30):
        """Получить статистику платежей за указанный период"""
        try:
            async with self.pool.acquire() as conn:
                stats = await conn.fetchrow(f'''
                    SELECT 
                        COUNT(*) as total_payments,
                        COUNT(*) FILTER (WHERE status = 'succeeded') as successful_payments,
                        COUNT(*) FILTER (WHERE status = 'pending') as pending_payments,
                        COALESCE(SUM(amount) FILTER (WHERE status = 'succeeded'), 0) as total_revenue,
                        COALESCE(AVG(amount) FILTER (WHERE status = 'succeeded'), 0) as avg_payment
                    FROM payments
                    WHERE created_at >= NOW() - INTERVAL '{days} days'
                ''')
                return dict(stats) if stats else {}
        except Exception as e:
            logger.error(f"Ошибка get_payments_statistics: {e}")
            return {}
    
    async def create_subscription(self, user_id: int, plan_key: str, payment_id: str):
        """Создать подписку после успешного платежа"""
        try:
            async with self.pool.acquire() as conn:
                plan = Config.SUBSCRIPTION_PLANS.get(plan_key)
                if not plan:
                    return False
                
                # Деактивируем старые подписки пользователя
                await conn.execute(
                    'UPDATE subscriptions SET is_active = FALSE WHERE user_id = $1',
                    user_id
                )
                
                # Создаем новую подписку - ИСПРАВЛЕНО: используем duration_months из плана
                subscription = await conn.fetchrow(
                    '''
                    INSERT INTO subscriptions (
                        user_id, plan_key, request_limit, used_requests, end_date, is_active
                    )
                    VALUES ($1, $2, $3, 0, NOW() + INTERVAL '1 month' * $4, TRUE)
                    RETURNING *
                    ''',
                    user_id, 
                    plan_key, 
                    plan['requests'], 
                    plan.get('duration_months', plan['days'] // 30)  # Преобразуем дни в месяцы
                )
                
                # Обновляем статус платежа
                await conn.execute(
                    '''
                    UPDATE payments 
                    SET status = 'succeeded', 
                        subscription_id = $1,
                        updated_at = NOW()
                    WHERE payment_id = $2
                    ''',
                    subscription['id'], payment_id
                )
                
                return True
        except Exception as e:
            logger.error(f"Ошибка create_subscription: {e}")
            return False
    
    async def create_payment_record(self, user_id: int, payment_id: str, amount: float, plan_key: str):
        """Создать запись о платеже"""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute(
                    '''
                    INSERT INTO payments (user_id, payment_id, amount, plan_key, status)
                    VALUES ($1, $2, $3, $4, 'pending')
                    ''',
                    user_id, payment_id, amount, plan_key
                )
                return True
        except Exception as e:
            logger.error(f"Ошибка create_payment_record: {e}")
            return False
    
    async def update_payment_status(self, payment_id: str, status: str):
        """Обновить статус платежа"""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute(
                    '''
                    UPDATE payments 
                    SET status = $1, updated_at = NOW()
                    WHERE payment_id = $2
                    ''',
                    status, payment_id
                )
                return True
        except Exception as e:
            logger.error(f"Ошибка update_payment_status: {e}")
            return False
    
    async def get_payment_by_yookassa_id(self, yookassa_payment_id: str):
        """Получить платеж по ID из Яндекс Кассы"""
        try:
            async with self.pool.acquire() as conn:
                payment = await conn.fetchrow(
                    'SELECT * FROM payments WHERE payment_id = $1',
                    yookassa_payment_id
                )
                return dict(payment) if payment else None
        except Exception as e:
            logger.error(f"Ошибка get_payment_by_yookassa_id: {e}")
            return None
    
    async def get_active_subscription(self, user_id: int):
        """Получить активную подписку пользователя"""
        try:
            async with self.pool.acquire() as conn:
                subscription = await conn.fetchrow(
                    '''
                    SELECT * FROM subscriptions 
                    WHERE user_id = $1 AND is_active = TRUE 
                    AND (end_date IS NULL OR end_date > NOW())
                    ORDER BY end_date DESC LIMIT 1
                    ''',
                    user_id
                )
                return dict(subscription) if subscription else None
        except Exception as e:
            logger.error(f"Ошибка get_active_subscription: {e}")
            return None
    
    async def get_user_by_telegram_id(self, telegram_id: int):
        """Получить пользователя по Telegram ID"""
        try:
            async with self.pool.acquire() as conn:
                user = await conn.fetchrow(
                    'SELECT * FROM users WHERE telegram_id = $1',
                    telegram_id
                )
                return dict(user) if user else None
        except Exception as e:
            logger.error(f"Ошибка get_user_by_telegram_id: {e}")
            return None
    
    async def get_payments_by_user(self, user_id: int, limit: int = 10):
        """Получить платежи пользователя"""
        try:
            async with self.pool.acquire() as conn:
                payments = await conn.fetch(
                    '''
                    SELECT * FROM payments 
                    WHERE user_id = $1 
                    ORDER BY created_at DESC 
                    LIMIT $2
                    ''',
                    user_id, limit
                )
                return [dict(p) for p in payments]
        except Exception as e:
            logger.error(f"Ошибка get_payments_by_user: {e}")
            return []
    
    async def add_default_instructions(self):
        """Добавить инструкции по умолчанию (если таблица пуста)"""
        try:
            async with self.pool.acquire() as conn:
                count = await conn.fetchval('SELECT COUNT(*) FROM instructions')
                
                if count == 0:
                    default_instructions = [
                        ("📋 Как пользоваться ботом", 
                         "1. Нажмите '💎 Купить подписку'\n"
                         "2. Выберите тарифный план\n"
                         "3. Оплатите через Яндекс Кассу\n"
                         "4. После активации нажмите '🔗 Добавить ссылку'\n"
                         "5. Отправьте ссылку для сохранения"),
                        
                        ("💎 О тарифных планах", 
                         "• Запрос = добавление одной ссылки\n"
                         "• Лимит обновляется при продлении подписки\n"
                         "• Можно добавлять только http/https ссылки\n"
                         "• Подписка автоматически деактивируется после окончания срока"),
                        
                        ("⚠️ Важная информация", 
                         "• После оплаты подписка активируется автоматически\n"
                         "• Обычно активация занимает 1-2 минуты\n"
                         "• Статус можно проверить в '📊 Моя статистика'\n"
                         "• При проблемах обратитесь в поддержку")
                    ]
                    
                    for title, content in default_instructions:
                        await conn.execute(
                            'INSERT INTO instructions (title, text_content) VALUES ($1, $2)',
                            title, content
                        )
                    
                    logger.info("✅ Добавлены инструкции по умолчанию")
        except Exception as e:
            logger.error(f"Ошибка add_default_instructions: {e}")
    
    async def get_all_users(self, limit: int = 50):
        """Получить всех пользователей"""
        try:
            async with self.pool.acquire() as conn:
                users = await conn.fetch(
                    '''
                    SELECT 
                        u.*,
                        COUNT(DISTINCT s.id) as total_subscriptions,
                        COUNT(DISTINCT p.id) as total_payments,
                        MAX(s.end_date) as last_subscription_end
                    FROM users u
                    LEFT JOIN subscriptions s ON u.id = s.user_id
                    LEFT JOIN payments p ON u.id = p.user_id
                    GROUP BY u.id
                    ORDER BY u.created_at DESC
                    LIMIT $1
                    ''',
                    limit
                )
                return [dict(u) for u in users]
        except Exception as e:
            logger.error(f"Ошибка get_all_users: {e}")
            return []

# Создаем глобальный экземпляр базы данных
db = Database()