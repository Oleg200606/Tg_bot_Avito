import psycopg2
from psycopg2 import pool
from flask import current_app
import logging

logger = logging.getLogger(__name__)

connection_pool = None

def init_db(app):
    """Инициализация пула соединений с базой данных"""
    global connection_pool
    
    try:
        connection_pool = psycopg2.pool.SimpleConnectionPool(
            1, 20,
            host=app.config['DB_HOST'],
            port=app.config['DB_PORT'],
            database=app.config['DB_NAME'],
            user=app.config['DB_USER'],
            password=app.config['DB_PASSWORD']
        )
        logger.info("Database connection pool created successfully")
    except Exception as e:
        logger.error(f"Error creating connection pool: {e}")
        raise

def get_connection():
    """Получение соединения из пула"""
    try:
        return connection_pool.getconn()
    except Exception as e:
        logger.error(f"Error getting connection: {e}")
        raise

def return_connection(conn):
    """Возврат соединения в пул"""
    try:
        connection_pool.putconn(conn)
    except Exception as e:
        logger.error(f"Error returning connection: {e}")

def execute_query(query, params=None, fetch=False, fetch_one=False):
    """Выполнение SQL запроса"""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute(query, params or ())
        
        if fetch:
            result = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in result]
        elif fetch_one:
            result = cursor.fetchone()
            if result:
                columns = [desc[0] for desc in cursor.description]
                return dict(zip(columns, result))
            return None
        
        conn.commit()
        return True
        
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Error executing query: {e}")
        raise
    finally:
        if conn:
            cursor.close()
            return_connection(conn)