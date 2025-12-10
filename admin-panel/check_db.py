import asyncpg
import asyncio
import os

DB_CONFIG = {
    'host': os.getenv("DB_HOST", "postgres"),
    'port': os.getenv("DB_PORT", "5432"),
    'database': os.getenv("DB_NAME", "avito_bot"),
    'user': os.getenv("DB_USER", "postgres"),
    'password': os.getenv("DB_PASSWORD", "1")
}

async def check_tables():
    conn = await asyncpg.connect(**DB_CONFIG)
    try:
        # Проверяем структуру таблицы subscriptions
        print("=== Структура таблицы subscriptions ===")
        result = await conn.fetch("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'subscriptions'
            ORDER BY ordinal_position
        """)
        
        for row in result:
            print(f"{row['column_name']}: {row['data_type']} ({'NULL' if row['is_nullable'] == 'YES' else 'NOT NULL'})")
        
        print("\n=== Содержимое таблицы subscriptions (первые 5 строк) ===")
        data = await conn.fetch("SELECT * FROM subscriptions LIMIT 5")
        for row in data:
            print(dict(row))
            
        print("\n=== Структура таблицы users ===")
        result = await conn.fetch("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'users'
            ORDER BY ordinal_position
        """)
        
        for row in result:
            print(f"{row['column_name']}: {row['data_type']} ({'NULL' if row['is_nullable'] == 'YES' else 'NOT NULL'})")
            
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(check_tables())