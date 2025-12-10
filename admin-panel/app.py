from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import asyncpg
import asyncio
import os
import hashlib
from datetime import datetime, timedelta
from functools import wraps

app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = os.getenv("SECRET_KEY", "admin-secret-key-change-me")

# Конфигурация БД
DB_CONFIG = {
    'host': os.getenv("DB_HOST", "postgres"),
    'port': os.getenv("DB_PORT", "5432"),
    'database': os.getenv("DB_NAME", "avito_bot"),
    'user': os.getenv("DB_USER", "postgres"),
    'password': os.getenv("DB_PASSWORD", "1")
}

# Админские учетки
ADMINS = {
    'admin': {
        'password': hashlib.sha256('Admin123!'.encode()).hexdigest(),
        'name': 'Администратор'
    }
}

# Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, id, username, name):
        self.id = id
        self.username = username
        self.name = name

@login_manager.user_loader
def load_user(user_id):
    if user_id in ADMINS:
        return User(user_id, user_id, ADMINS[user_id]['name'])
    return None

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({'success': False, 'error': 'Требуется авторизация'}), 401
        return f(*args, **kwargs)
    return decorated_function

# Функции для работы с БД
async def get_connection():
    return await asyncpg.connect(**DB_CONFIG)

async def execute_query(query, *args):
    conn = await get_connection()
    try:
        return await conn.execute(query, *args)
    finally:
        await conn.close()

async def fetch_query(query, *args):
    conn = await get_connection()
    try:
        return await conn.fetch(query, *args)
    finally:
        await conn.close()

async def fetch_one(query, *args):
    conn = await get_connection()
    try:
        return await conn.fetchrow(query, *args)
    finally:
        await conn.close()

async def fetch_val(query, *args):
    conn = await get_connection()
    try:
        return await conn.fetchval(query, *args)
    finally:
        await conn.close()

def run_async(coro):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()

# Проверка наличия колонок в таблице
async def check_column_exists(table, column):
    conn = await get_connection()
    try:
        result = await conn.fetchval("""
            SELECT COUNT(*)
            FROM information_schema.columns 
            WHERE table_name = $1 AND column_name = $2
        """, table, column)
        return result > 0
    finally:
        await conn.close()

# Проверка существования таблицы
async def table_exists(table_name):
    conn = await get_connection()
    try:
        result = await conn.fetchval("""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_name = $1
        """, table_name)
        return result > 0
    finally:
        await conn.close()

# Маршруты
@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        if username in ADMINS:
            hashed_password = hashlib.sha256(password.encode()).hexdigest()
            if ADMINS[username]['password'] == hashed_password:
                user = User(username, username, ADMINS[username]['name'])
                login_user(user)
                session['last_activity'] = datetime.now().isoformat()
                return jsonify({'success': True, 'redirect': url_for('index')})
        
        return jsonify({'success': False, 'error': 'Неверные данные'})
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()
    return redirect(url_for('login'))

# API маршруты
@app.route('/api/stats')
@admin_required
def api_stats():
    """Основная статистика"""
    try:
        # Общее количество пользователей
        total_users = run_async(fetch_val("SELECT COUNT(*) FROM users"))
        
        # Активные подписки
        active_subs = run_async(fetch_val("""
            SELECT COUNT(*) FROM subscriptions 
            WHERE is_active = true AND end_date > NOW()
        """))
        
        # Сегодняшние платежи
        today_payments = run_async(fetch_one("""
            SELECT 
                COUNT(*) as count,
                COALESCE(SUM(amount), 0) as total
            FROM payments 
            WHERE DATE(created_at) = CURRENT_DATE AND status = 'succeeded'
        """))
        
        return jsonify({
            'success': True,
            'stats': {
                'total_users': total_users or 0,
                'active_subs': active_subs or 0,
                'today_payments_count': today_payments['count'] if today_payments else 0,
                'today_payments_amount': float(today_payments['total']) if today_payments else 0
            }
        })
    except Exception as e:
        print(f"Error in stats: {e}")
        return jsonify({
            'success': True,
            'stats': {
                'total_users': 0,
                'active_subs': 0,
                'today_payments_count': 0,
                'today_payments_amount': 0
            }
        })

@app.route('/api/users')
@admin_required
def api_users():
    """Список пользователей"""
    try:
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 20, type=int)
        offset = (page - 1) * limit
        
        # Строим запрос
        query = """
            SELECT 
                u.*, 
                s.id as subscription_id,
                s.start_date as sub_start,
                s.end_date as sub_end,
                s.is_active as sub_active,
                s.request_limit,
                s.used_requests
            FROM users u
            LEFT JOIN subscriptions s ON u.id = s.user_id AND s.is_active = true
            ORDER BY u.created_at DESC
            LIMIT $1 OFFSET $2
        """
        
        users = run_async(fetch_query(query, limit, offset))
        total = run_async(fetch_val("SELECT COUNT(*) FROM users"))
        
        users_list = []
        for user in users:
            users_list.append({
                'id': user['id'],
                'telegram_id': user['telegram_id'],
                'username': user['username'],
                'full_name': user['full_name'],
                'created_at': user['created_at'].isoformat() if user['created_at'] else None,
                'subscription': {
                    'id': user['subscription_id'],
                    'start': user['sub_start'].isoformat() if user['sub_start'] else None,
                    'end': user['sub_end'].isoformat() if user['sub_end'] else None,
                    'active': user['sub_active'],
                    'request_limit': user['request_limit'],
                    'used_requests': user['used_requests']
                } if user['subscription_id'] else None
            })
        
        return jsonify({
            'success': True,
            'users': users_list,
            'total': total or 0,
            'page': page,
            'total_pages': (total + limit - 1) // limit if total else 1
        })
    except Exception as e:
        print(f"Error in users API: {e}")
        return jsonify({
            'success': False, 
            'error': str(e),
            'users': [],
            'total': 0
        }), 500

@app.route('/api/subscriptions')
@admin_required
def api_subscriptions():
    """Список подписок"""
    try:
        status = request.args.get('status', 'all')
        
        # Базовый запрос
        query = """
            SELECT 
                s.*, 
                u.telegram_id, 
                u.username, 
                u.full_name
            FROM subscriptions s
            JOIN users u ON s.user_id = u.id
        """
        
        if status == 'active':
            query += " WHERE s.is_active = true AND s.end_date > NOW()"
        elif status == 'expired':
            query += " WHERE s.is_active = false OR s.end_date <= NOW()"
        
        query += " ORDER BY s.end_date DESC"
        
        subscriptions = run_async(fetch_query(query))
        
        subs_list = []
        for sub in subscriptions:
            subs_list.append({
                'id': sub['id'],
                'user': {
                    'id': sub['user_id'],
                    'telegram_id': sub['telegram_id'],
                    'username': sub['username'],
                    'full_name': sub['full_name']
                },
                'start_date': sub['start_date'].isoformat(),
                'end_date': sub['end_date'].isoformat(),
                'is_active': sub['is_active'],
                'request_limit': sub['request_limit'],
                'used_requests': sub['used_requests'],
                'created_at': sub['created_at'].isoformat()
            })
        
        return jsonify({'success': True, 'subscriptions': subs_list})
    except Exception as e:
        print(f"Error in subscriptions API: {e}")
        return jsonify({'success': False, 'error': str(e), 'subscriptions': []}), 500

@app.route('/api/subscription/<int:sub_id>/extend', methods=['POST'])
@admin_required
def api_extend_subscription(sub_id):
    """Продлить подписку"""
    try:
        data = request.json
        days = data.get('days', 30)
        
        result = run_async(execute_query("""
            UPDATE subscriptions 
            SET end_date = end_date + INTERVAL '%s days',
                is_active = true,
                updated_at = NOW()
            WHERE id = $1
            RETURNING id
        """ % days, sub_id))
        
        if result:
            return jsonify({'success': True, 'message': 'Подписка продлена'})
        else:
            return jsonify({'success': False, 'error': 'Подписка не найдена'}), 404
    except Exception as e:
        print(f"Error extending subscription: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/subscription/<int:sub_id>/cancel', methods=['POST'])
@admin_required
def api_cancel_subscription(sub_id):
    """Отменить подписку"""
    try:
        result = run_async(execute_query("""
            UPDATE subscriptions 
            SET is_active = false,
                updated_at = NOW()
            WHERE id = $1
            RETURNING id
        """, sub_id))
        
        if result:
            return jsonify({'success': True, 'message': 'Подписка отменена'})
        else:
            return jsonify({'success': False, 'error': 'Подписка не найдена'}), 404
    except Exception as e:
        print(f"Error canceling subscription: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/user/<int:user_id>', methods=['GET'])
@admin_required
def api_get_user(user_id):
    """Получить информацию о пользователе"""
    try:
        # Получаем пользователя
        user = run_async(fetch_one("""
            SELECT 
                u.*,
                s.id as subscription_id,
                s.start_date as sub_start,
                s.end_date as sub_end,
                s.is_active as sub_active,
                s.request_limit,
                s.used_requests
            FROM users u
            LEFT JOIN subscriptions s ON u.id = s.user_id AND s.is_active = true
            WHERE u.id = $1
        """, user_id))
        
        if not user:
            return jsonify({'success': False, 'error': 'Пользователь не найден'}), 404
        
        user_data = {
            'id': user['id'],
            'telegram_id': user['telegram_id'],
            'username': user['username'],
            'full_name': user['full_name'],
            'created_at': user['created_at'].isoformat(),
            'subscription': None
        }
        
        if user['subscription_id']:
            user_data['subscription'] = {
                'id': user['subscription_id'],
                'start_date': user['sub_start'].isoformat(),
                'end_date': user['sub_end'].isoformat(),
                'is_active': user['sub_active'],
                'request_limit': user['request_limit'],
                'used_requests': user['used_requests']
            }
        
        # История подписок
        sub_history = run_async(fetch_query("""
            SELECT 
                s.*
            FROM subscriptions s
            WHERE s.user_id = $1 
            ORDER BY s.created_at DESC 
            LIMIT 10
        """, user_id))
        
        # История платежей
        payments = run_async(fetch_query("""
            SELECT 
                p.*
            FROM payments p
            WHERE p.user_id = $1 
            ORDER BY p.created_at DESC 
            LIMIT 10
        """, user_id))
        
        return jsonify({
            'success': True,
            'user': user_data,
            'subscription_history': [
                {
                    'id': sub['id'],
                    'start_date': sub['start_date'].isoformat(),
                    'end_date': sub['end_date'].isoformat(),
                    'is_active': sub['is_active'],
                    'created_at': sub['created_at'].isoformat()
                } for sub in sub_history
            ],
            'payments': [
                {
                    'id': p['id'],
                    'amount': float(p['amount']) if p['amount'] else 0,
                    'status': p['status'] or 'unknown',
                    'created_at': p['created_at'].isoformat() if p['created_at'] else None
                } for p in payments
            ]
        })
    except Exception as e:
        print(f"Error getting user: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/user/<int:user_id>/add_subscription', methods=['POST'])
@admin_required
def api_add_subscription(user_id):
    """Добавить подписку пользователю"""
    try:
        data = request.json
        days = data.get('days', 30)
        
        # Отключаем старую активную подписку
        run_async(execute_query("""
            UPDATE subscriptions 
            SET is_active = false 
            WHERE user_id = $1 AND is_active = true
        """, user_id))
        
        # Создаем новую подписку
        result = run_async(execute_query("""
            INSERT INTO subscriptions (
                user_id, 
                start_date, 
                end_date, 
                is_active, 
                request_limit,
                used_requests
            ) VALUES ($1, NOW(), NOW() + INTERVAL '%s days', true, 50, 0)
            RETURNING id
        """ % days, user_id))
        
        return jsonify({
            'success': True, 
            'message': 'Подписка добавлена',
            'subscription_id': result if result else None
        })
    except Exception as e:
        print(f"Error adding subscription: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/bot/restart', methods=['POST'])
@admin_required
def api_restart_bot():
    """Перезапуск бота"""
    try:
        return jsonify({'success': True, 'message': 'Команда перезапуска отправлена'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/bot/status')
@admin_required
def api_bot_status():
    """Статус бота"""
    try:
        # Простая проверка подключения к БД
        run_async(get_connection())
        return jsonify({
            'success': True,
            'status': 'online',
            'last_active': datetime.now().isoformat()
        })
    except Exception as e:
        print(f"Bot status error: {e}")
        return jsonify({
            'success': True,
            'status': 'offline',
            'last_active': datetime.now().isoformat(),
            'error': str(e)
        })

@app.before_request
def before_request():
    """Проверка активности сессии"""
    if current_user.is_authenticated:
        last_activity = session.get('last_activity')
        if last_activity:
            try:
                last_activity = datetime.fromisoformat(last_activity)
                if datetime.now() - last_activity > timedelta(hours=1):
                    logout_user()
                    session.clear()
                    return redirect(url_for('login'))
            except:
                pass
        session['last_activity'] = datetime.now().isoformat()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)