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

async def check_database():
    conn = await asyncpg.connect(**DB_CONFIG)
    try:
        print("=== ВСЕ ТАБЛИЦЫ ===")
        tables = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        for table in tables:
            print(f"• {table['table_name']}")
        
        print("\n=== СТРУКТУРА subscriptions ===")
        columns = await conn.fetch("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'subscriptions'
            ORDER BY ordinal_position
        """)
        for col in columns:
            print(f"  {col['column_name']} ({col['data_type']}) - {'NULL' if col['is_nullable'] == 'YES' else 'NOT NULL'}")
        
        print("\n=== ПРИМЕР ДАННЫХ subscriptions ===")
        data = await conn.fetch("SELECT * FROM subscriptions LIMIT 3")
        for row in data:
            print(dict(row))
        
        print("\n=== СТРУКТУРА tariff_plans ===")
        columns = await conn.fetch("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'tariff_plans'
            ORDER BY ordinal_position
        """)
        if columns:
            for col in columns:
                print(f"  {col['column_name']} ({col['data_type']}) - {'NULL' if col['is_nullable'] == 'YES' else 'NOT NULL'}")
        else:
            print("  Таблица tariff_plans не существует!")
            
        print("\n=== ПРИМЕР ДАННЫХ users ===")
        data = await conn.fetch("SELECT * FROM users LIMIT 3")
        for row in data:
            print(dict(row))
            
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(check_database())