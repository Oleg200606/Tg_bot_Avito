import asyncpg
import asyncio
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from bot.config import Config

class Database:
    def __init__(self):
        self.pool = None
    
    async def connect(self):
        self.pool = await asyncpg.create_pool(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            database=Config.DB_NAME,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD
        )
    
    async def create_tables(self):
        async with self.pool.acquire() as conn:
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
    
    async def get_or_create_user(self, telegram_id: int, username: str, full_name: str):
        async with self.pool.acquire() as conn:
            user = await conn.fetchrow(
                'SELECT * FROM users WHERE telegram_id = $1',
                telegram_id
            )
            
            if not user:
                user = await conn.fetchrow(
                    '''INSERT INTO users (telegram_id, username, full_name, is_admin)
                       VALUES ($1, $2, $3, $4) RETURNING *''',
                    telegram_id, username, full_name, telegram_id in Config.ADMIN_IDS
                )
            
            return dict(user) if user else None
    
    async def check_subscription(self, user_id: int) -> bool:
        async with self.pool.acquire() as conn:
            subscription = await conn.fetchrow(
                '''SELECT * FROM subscriptions 
                   WHERE user_id = $1 AND is_active = TRUE 
                   AND end_date > CURRENT_TIMESTAMP''',
                user_id
            )
            return subscription is not None
    
    async def create_subscription(self, user_id: int, days: int, payment_id: str, plan: str = "basic"):
        async with self.pool.acquire() as conn:
            start_date = datetime.now()
            end_date = start_date + timedelta(days=days)
            
            # Деактивируем старые подписки
            await conn.execute(
                'UPDATE subscriptions SET is_active = FALSE WHERE user_id = $1',
                user_id
            )
            
            # Создаем новую подписку
            subscription = await conn.fetchrow(
                '''INSERT INTO subscriptions 
                   (user_id, start_date, end_date, payment_id, plan)
                   VALUES ($1, $2, $3, $4, $5) RETURNING *''',
                user_id, start_date, end_date, payment_id, plan
            )
            
            return dict(subscription) if subscription else None
    
    async def add_user_link(self, user_id: int, link: str):
        async with self.pool.acquire() as conn:
            await conn.execute(
                'INSERT INTO user_links (user_id, link) VALUES ($1, $2)',
                user_id, link
            )
    
    async def get_user_links(self, user_id: int):
        async with self.pool.acquire() as conn:
            links = await conn.fetch(
                'SELECT * FROM user_links WHERE user_id = $1 ORDER BY created_at DESC',
                user_id
            )
            return [dict(link) for link in links]
    
    async def get_instructions(self):
        async with self.pool.acquire() as conn:
            instructions = await conn.fetch(
                'SELECT * FROM instructions ORDER BY order_index ASC'
            )
            return [dict(instruction) for instruction in instructions]
    
    async def add_instruction(self, title: str, text_content: str, video_url: str):
        async with self.pool.acquire() as conn:
            max_order = await conn.fetchval('SELECT MAX(order_index) FROM instructions') or 0
            instruction = await conn.fetchrow(
                '''INSERT INTO instructions (title, text_content, video_url, order_index)
                   VALUES ($1, $2, $3, $4) RETURNING *''',
                title, text_content, video_url, max_order + 1
            )
            return dict(instruction) if instruction else None
    
    async def get_statistics(self):
        async with self.pool.acquire() as conn:
            stats = await conn.fetchrow('''
                SELECT 
                    COUNT(DISTINCT u.id) as total_users,
                    COUNT(DISTINCT s.user_id) as active_subscribers,
                    COUNT(DISTINCT CASE WHEN s.end_date > CURRENT_TIMESTAMP THEN s.user_id END) as current_subscribers,
                    COALESCE(SUM(CASE WHEN p.status = 'succeeded' THEN p.amount ELSE 0 END), 0) as total_revenue
                FROM users u
                LEFT JOIN subscriptions s ON u.id = s.user_id
                LEFT JOIN payments p ON u.id = p.user_id
            ''')
            return dict(stats) if stats else {}
    
    async def get_all_users(self):
        async with self.pool.acquire() as conn:
            users = await conn.fetch('''
                SELECT u.*, 
                       MAX(s.end_date) as subscription_end,
                       s.is_active as has_active_sub
                FROM users u
                LEFT JOIN subscriptions s ON u.id = s.user_id AND s.is_active = TRUE
                GROUP BY u.id, s.is_active
                ORDER BY u.created_at DESC
            ''')
            return [dict(user) for user in users]

db = Database()