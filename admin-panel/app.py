from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash, make_response, send_from_directory
# Добавьте этот patch в начало файла
import werkzeug.urls
if not hasattr(werkzeug.urls, 'url_decode'):
    from werkzeug.datastructures import MultiDict
    from urllib.parse import parse_qsl
    werkzeug.urls.url_decode = lambda s: MultiDict(parse_qsl(s, keep_blank_values=True))

from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_cors import CORS
from functools import wraps
import asyncpg
import asyncio
from datetime import datetime, timedelta
import json
import os
import hashlib
import csv
import io

app = Flask(__name__, static_folder='static')
CORS(app)
app.secret_key = os.getenv("SECRET_KEY", "secret-key-change-in-production")

# Настройки базы данных
DB_CONFIG = {
    'host': os.getenv("DB_HOST", "postgres"),
    'port': os.getenv("DB_PORT", "5432"),
    'database': os.getenv("DB_NAME", "avito_bot"),
    'user': os.getenv("DB_USER", "postgres"),
    'password': os.getenv("DB_PASSWORD", "1")
}

# Админские учетные данные
ADMINS = {
    'admin': {
        'password_hash': hashlib.sha256('Admin123!'.encode()).hexdigest(),
        'name': 'Главный администратор',
        'role': 'Супер админ'
    }
}

# Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Пожалуйста, войдите для доступа к этой странице'
login_manager.login_message_category = 'error'

class User(UserMixin):
    def __init__(self, id, username, name, role):
        self.id = id
        self.username = username
        self.name = name
        self.role = role

@login_manager.user_loader
def load_user(user_id):
    if user_id in ADMINS:
        return User(user_id, user_id, ADMINS[user_id]['name'], ADMINS[user_id].get('role', 'Администратор'))
    return None

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({'success': False, 'error': 'Требуется авторизация'}), 401
        return f(*args, **kwargs)
    return decorated_function

# Helper functions for async DB operations
def run_async(coro, *args, **kwargs):
    """Запуск асинхронной функции с аргументами"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        if args or kwargs:
            # Если есть аргументы
            return loop.run_until_complete(coro(*args, **kwargs))
        else:
            return loop.run_until_complete(coro)
    finally:
        loop.close()

async def get_connection():
    return await asyncpg.connect(**DB_CONFIG)

async def fetch_query(query, *args):
    conn = await get_connection()
    try:
        return await conn.fetch(query, *args)
    finally:
        await conn.close()

async def execute_query(query, *args):
    conn = await get_connection()
    try:
        return await conn.execute(query, *args)
    finally:
        await conn.close()

async def fetch_val(query, *args):
    conn = await get_connection()
    try:
        return await conn.fetchval(query, *args)
    finally:
        await conn.close()

async def fetch_one(query, *args):
    conn = await get_connection()
    try:
        return await conn.fetchrow(query, *args)
    finally:
        await conn.close()

# Routes
@app.route('/')
def index():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
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
            if ADMINS[username]['password_hash'] == hashed_password:
                user = User(username, username, ADMINS[username]['name'], ADMINS[username].get('role', 'Администратор'))
                login_user(user)
                session['last_activity'] = datetime.now().isoformat()
                return jsonify({'success': True, 'redirect': url_for('index')})
        
        return jsonify({'success': False, 'error': 'Неверное имя пользователя или пароль'})
    
    return render_template('login.html')

@app.route('/logout', methods=['GET', 'POST'])
@admin_required
def logout():
    """Выход из системы"""
    logout_user()
    session.clear()
    if request.method == 'POST':
        return jsonify({'success': True, 'redirect': url_for('login')})
    return redirect(url_for('login'))

@app.route('/api/admin/current')
@admin_required
def get_current_admin():
    return jsonify({
        'success': True,
        'admin': {
            'name': current_user.name,
            'role': current_user.role,
            'username': current_user.username
        }
    })

# API Endpoints
@app.route('/api/dashboard/stats')
@admin_required
def api_dashboard_stats():
    """Статистика для дашборда"""
    try:
        # Основная статистика
        stats_query = '''
            SELECT 
                COUNT(DISTINCT u.id) as total_users,
                COUNT(DISTINCT CASE WHEN s.end_date > CURRENT_TIMESTAMP THEN s.user_id END) as active_subscribers,
                COUNT(DISTINCT ul.user_id) as users_with_links,
                COUNT(ul.id) as total_links
            FROM users u
            LEFT JOIN subscriptions s ON u.id = s.user_id AND s.is_active = TRUE
            LEFT JOIN user_links ul ON u.id = ul.user_id
        '''
        stats_result = run_async(fetch_query, stats_query)
        stats = dict(stats_result[0]) if stats_result else {}
        
        # Статистика по дням (30 дней)
        daily_query = '''
            SELECT 
                DATE(created_at) as date,
                COUNT(*) as new_users,
                COUNT(CASE WHEN EXISTS (
                    SELECT 1 FROM subscriptions s 
                    WHERE s.user_id = u.id 
                    AND DATE(s.start_date) = DATE(u.created_at)
                    AND s.is_active = TRUE
                ) THEN 1 END) as new_subscriptions
            FROM users u
            WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
            GROUP BY DATE(created_at)
            ORDER BY date ASC
        '''
        daily_result = run_async(fetch_query, daily_query)
        daily_stats = [dict(row) for row in daily_result]
        
        # Конверсия
        conversion = 0
        if stats.get('total_users', 0) > 0:
            conversion = (stats.get('active_subscribers', 0) / stats.get('total_users', 1)) * 100
        
        return jsonify({
            'success': True,
            'stats': {
                **stats,
                'conversion_rate': round(conversion, 1)
            },
            'daily_stats': daily_stats
        })
    except Exception as e:
        app.logger.error(f"Error in dashboard stats: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/dashboard/recent-activity')
@admin_required
def api_recent_activity():
    """Последняя активность"""
    try:
        # Активность пользователей
        activity_query = '''
            SELECT 
                u.full_name as user_name,
                'Зарегистрировался' as action,
                u.created_at as time,
                'info' as status
            FROM users u
            WHERE u.created_at >= CURRENT_DATE - INTERVAL '7 days'
            
            UNION ALL
            
            SELECT 
                u.full_name as user_name,
                'Купил подписку' as action,
                s.start_date as time,
                'success' as status
            FROM subscriptions s
            JOIN users u ON s.user_id = u.id
            WHERE s.start_date >= CURRENT_DATE - INTERVAL '7 days'
            AND s.is_active = TRUE
            
            UNION ALL
            
            SELECT 
                u.full_name as user_name,
                'Добавил ссылку' as action,
                ul.created_at as time,
                'success' as status
            FROM user_links ul
            JOIN users u ON ul.user_id = u.id
            WHERE ul.created_at >= CURRENT_DATE - INTERVAL '7 days'
            
            ORDER BY time DESC
            LIMIT 10
        '''
        
        activities = run_async(fetch_query, activity_query)
        
        activities_list = []
        for activity in activities:
            activity_dict = dict(activity)
            
            # Форматирование времени
            time_diff = datetime.now() - activity_dict['time']
            if time_diff.total_seconds() < 3600:
                time_str = f"{int(time_diff.total_seconds() / 60)} минут назад"
            elif time_diff.total_seconds() < 86400:
                time_str = f"{int(time_diff.total_seconds() / 3600)} часов назад"
            else:
                time_str = activity_dict['time'].strftime('%d.%m.%Y %H:%M')
            
            activity_dict['time'] = time_str
            activities_list.append(activity_dict)
        
        return jsonify({
            'success': True,
            'activities': activities_list
        })
    except Exception as e:
        app.logger.error(f"Error in recent activity: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/users')
@admin_required
def api_users():
    """Список пользователей"""
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        search = request.args.get('search', '')
        filter_type = request.args.get('filter', '')
        offset = (page - 1) * limit
        
        # Базовый запрос
        query = '''
            SELECT 
                u.*,
                MAX(s.end_date) as subscription_end,
                BOOL_OR(s.is_active AND s.end_date > CURRENT_TIMESTAMP) as has_active_sub,
                COUNT(ul.id) as links_count,
                EXISTS(SELECT 1 FROM subscriptions s2 
                       WHERE s2.user_id = u.id 
                       AND s2.is_active = TRUE 
                       AND s2.end_date > CURRENT_TIMESTAMP) as is_active_subscriber
            FROM users u
            LEFT JOIN subscriptions s ON u.id = s.user_id
            LEFT JOIN user_links ul ON u.id = ul.user_id
        '''
        
        params = []
        where_clauses = []
        param_counter = 1
        
        if search:
            where_clauses.append(f'''
                (u.telegram_id::TEXT ILIKE ${param_counter} OR 
                u.username ILIKE ${param_counter} OR 
                u.full_name ILIKE ${param_counter})
            ''')
            params.append(f'%{search}%')
            param_counter += 1
        
        if filter_type:
            if filter_type == 'active':
                where_clauses.append(f'''
                    EXISTS(SELECT 1 FROM subscriptions s2 
                           WHERE s2.user_id = u.id 
                           AND s2.is_active = TRUE 
                           AND s2.end_date > CURRENT_TIMESTAMP)
                ''')
            elif filter_type == 'inactive':
                where_clauses.append(f'''
                    NOT EXISTS(SELECT 1 FROM subscriptions s2 
                              WHERE s2.user_id = u.id 
                              AND s2.is_active = TRUE 
                              AND s2.end_date > CURRENT_TIMESTAMP)
                ''')
        
        if where_clauses:
            query += ' WHERE ' + ' AND '.join(where_clauses)
        
        query += f'''
            GROUP BY u.id
            ORDER BY u.created_at DESC
            LIMIT ${param_counter} OFFSET ${param_counter + 1}
        '''
        params.extend([limit, offset])
        
        users = run_async(fetch_query, query, *params)
        
        # Общее количество
        count_query = 'SELECT COUNT(DISTINCT u.id) FROM users u'
        if where_clauses:
            count_query += ' WHERE ' + ' AND '.join(where_clauses)
        
        total_result = run_async(fetch_query, count_query, *params[:len(params)-2])
        total = total_result[0]['count'] if total_result else 0
        
        users_list = []
        for user in users:
            user_dict = dict(user)
            # Преобразование datetime в строку
            for key, value in user_dict.items():
                if isinstance(value, datetime):
                    user_dict[key] = value.isoformat()
            users_list.append(user_dict)
        
        return jsonify({
            'success': True,
            'users': users_list,
            'total': total,
            'page': page,
            'total_pages': (total + limit - 1) // limit if limit > 0 else 1
        })
        
    except Exception as e:
        app.logger.error(f"Error in users API: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/user/<int:user_id>')
@admin_required
def api_user_details(user_id):
    """Детальная информация о пользователе"""
    try:
        # Информация о пользователе
        user_query = '''
            SELECT u.*,
                   COUNT(DISTINCT ul.id) as links_count,
                   COUNT(DISTINCT s.id) as subscriptions_count
            FROM users u
            LEFT JOIN user_links ul ON u.id = ul.user_id
            LEFT JOIN subscriptions s ON u.id = s.user_id
            WHERE u.id = $1
            GROUP BY u.id
        '''
        
        user_result = run_async(fetch_one, user_query, user_id)
        
        if not user_result:
            return jsonify({'success': False, 'error': 'Пользователь не найден'}), 404
        
        user_dict = dict(user_result)
        # Преобразование datetime в строку
        for key, value in user_dict.items():
            if isinstance(value, datetime):
                user_dict[key] = value.isoformat()
        
        # Подписки пользователя
        subs_query = '''
            SELECT s.*,
                   CASE 
                       WHEN s.end_date > CURRENT_TIMESTAMP THEN 'active'
                       ELSE 'expired'
                   END as status,
                   EXTRACT(DAY FROM (s.end_date - s.start_date))::INTEGER as duration_days
            FROM subscriptions s
            WHERE s.user_id = $1
            ORDER BY s.created_at DESC
        '''
        
        subscriptions = run_async(fetch_query, subs_query, user_id)
        subscriptions_list = [dict(sub) for sub in subscriptions]
        for sub in subscriptions_list:
            for key, value in sub.items():
                if isinstance(value, datetime):
                    sub[key] = value.isoformat()
        
        # Ссылки пользователя
        links_query = '''
            SELECT ul.*
            FROM user_links ul
            WHERE ul.user_id = $1
            ORDER BY ul.created_at DESC
            LIMIT 20
        '''
        
        links = run_async(fetch_query, links_query, user_id)
        links_list = [dict(link) for link in links]
        for link in links_list:
            for key, value in link.items():
                if isinstance(value, datetime):
                    link[key] = value.isoformat()
        
        return jsonify({
            'success': True,
            'user': user_dict,
            'subscriptions': subscriptions_list,
            'links': links_list
        })
        
    except Exception as e:
        app.logger.error(f"Error in user details: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/subscriptions')
@admin_required
def api_subscriptions():
    """Список подписок"""
    try:
        filter_type = request.args.get('filter', 'active')
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        offset = (page - 1) * limit
        
        base_query = '''
            SELECT 
                s.*,
                u.telegram_id,
                u.username,
                u.full_name,
                CASE 
                    WHEN s.end_date > CURRENT_TIMESTAMP THEN 'active'
                    ELSE 'expired'
                END as status,
                EXTRACT(DAY FROM (s.end_date - CURRENT_DATE))::INTEGER as days_left
            FROM subscriptions s
            JOIN users u ON s.user_id = u.id
            WHERE s.is_active = TRUE
        '''
        
        params = []
        where_clauses = []
        
        if filter_type == 'active':
            where_clauses.append('s.end_date > CURRENT_TIMESTAMP')
        elif filter_type == 'expired':
            where_clauses.append('s.end_date <= CURRENT_TIMESTAMP')
        
        query = base_query
        if where_clauses:
            query += ' AND ' + ' AND '.join(where_clauses)
        
        query += ' ORDER BY s.end_date DESC'
        query += f' LIMIT {limit} OFFSET {offset}'
        
        subscriptions = run_async(fetch_query, query, *params)
        
        # Общее количество
        count_query = f'SELECT COUNT(*) FROM ({query.replace(f"LIMIT {limit} OFFSET {offset}", "")}) as t'
        total_result = run_async(fetch_val, count_query, *params)
        total = total_result or 0
        
        subscriptions_list = []
        for sub in subscriptions:
            sub_dict = dict(sub)
            # Преобразование datetime в строку
            for key, value in sub_dict.items():
                if isinstance(value, datetime):
                    sub_dict[key] = value.isoformat()
                elif isinstance(value, timedelta):
                    sub_dict[key] = str(value.days) + ' дней'
            subscriptions_list.append(sub_dict)
        
        # Статистика подписок
        stats_query = '''
            SELECT 
                COUNT(*) as total_subscriptions,
                COUNT(CASE WHEN end_date > CURRENT_TIMESTAMP THEN 1 END) as active_subscriptions,
                COUNT(CASE WHEN end_date <= CURRENT_TIMESTAMP THEN 1 END) as expired_subscriptions,
                AVG(EXTRACT(DAY FROM (end_date - start_date))) as avg_duration
            FROM subscriptions
            WHERE is_active = TRUE
        '''
        
        stats_result = run_async(fetch_one, stats_query)
        stats = dict(stats_result) if stats_result else {}
        
        return jsonify({
            'success': True,
            'subscriptions': subscriptions_list,
            'stats': stats,
            'total': total,
            'page': page,
            'total_pages': (total + limit - 1) // limit if limit > 0 else 1
        })
        
    except Exception as e:
        app.logger.error(f"Error in subscriptions API: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/user/<int:user_id>/subscription', methods=['POST'])
@admin_required
def api_extend_subscription(user_id):
    """Продлить подписку пользователя"""
    try:
        data = request.json
        action = data.get('action', 'extend')
        days = int(data.get('days', 30))
        
        if action == 'extend':
            # Проверяем существующую подписку
            sub_query = '''
                SELECT * FROM subscriptions 
                WHERE user_id = $1 AND is_active = TRUE
                ORDER BY end_date DESC LIMIT 1
            '''
            existing_sub = run_async(fetch_one, sub_query, user_id)
            
            new_end_date = datetime.now() + timedelta(days=days)
            
            if existing_sub:
                # Обновляем существующую подписку
                update_query = '''
                    UPDATE subscriptions 
                    SET end_date = $1, updated_at = CURRENT_TIMESTAMP
                    WHERE id = $2
                    RETURNING *
                '''
                result = run_async(fetch_one, update_query, new_end_date, existing_sub['id'])
                message = f'Подписка продлена до {new_end_date.strftime("%d.%m.%Y")}'
            else:
                # Создаем новую подписку
                insert_query = '''
                    INSERT INTO subscriptions (user_id, start_date, end_date, is_active, plan)
                    VALUES ($1, CURRENT_TIMESTAMP, $2, TRUE, 'Продление из админки')
                    RETURNING *
                '''
                result = run_async(fetch_one, insert_query, user_id, new_end_date)
                message = f'Создана новая подписка до {new_end_date.strftime("%d.%m.%Y")}'
            
            return jsonify({
                'success': True,
                'message': message,
                'subscription': dict(result) if result else None
            })
        
        return jsonify({'success': False, 'error': 'Неизвестное действие'}), 400
        
    except Exception as e:
        app.logger.error(f"Error extending subscription: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/instructions')
@admin_required
def api_instructions():
    """Список инструкций"""
    try:
        instructions = run_async(fetch_query, '''
            SELECT * FROM instructions 
            ORDER BY order_index ASC, created_at DESC
        ''')
        
        instructions_list = []
        for inst in instructions:
            inst_dict = dict(inst)
            for key, value in inst_dict.items():
                if isinstance(value, datetime):
                    inst_dict[key] = value.isoformat()
            instructions_list.append(inst_dict)
        
        return jsonify({
            'success': True,
            'instructions': instructions_list
        })
    except Exception as e:
        app.logger.error(f"Error in instructions API: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/instructions', methods=['POST'])
@admin_required
def api_create_instruction():
    """Создание инструкции"""
    try:
        data = request.json
        title = data.get('title', '').strip()
        content = data.get('content', '').strip()
        video_url = data.get('video_url', '').strip()
        
        if not title or not content:
            return jsonify({'success': False, 'error': 'Заголовок и текст обязательны'}), 400
        
        # Получаем максимальный order_index
        max_order = run_async(fetch_val, 'SELECT COALESCE(MAX(order_index), 0) FROM instructions')
        
        result = run_async(execute_query, '''
            INSERT INTO instructions (title, text_content, video_url, order_index)
            VALUES ($1, $2, $3, $4)
        ''', title, content, video_url, max_order + 1)
        
        return jsonify({'success': True, 'message': 'Инструкция создана'})
        
    except Exception as e:
        app.logger.error(f"Error creating instruction: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/settings')
@admin_required
def api_get_settings():
    """Получить настройки"""
    try:
        # Здесь можно добавить получение настроек из БД
        settings = {
            'admin_ids': '123456789,987654321',
            'auto_renewal': 'enabled',
            'notify_new_users': True,
            'notify_expiring': True,
            'notify_errors': True
        }
        
        return jsonify({
            'success': True,
            'settings': settings
        })
    except Exception as e:
        app.logger.error(f"Error getting settings: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/settings', methods=['POST'])
@admin_required
def api_save_settings():
    """Сохранить настройки"""
    try:
        data = request.json
        # Здесь можно добавить сохранение настроек в БД
        return jsonify({
            'success': True,
            'message': 'Настройки сохранены'
        })
    except Exception as e:
        app.logger.error(f"Error saving settings: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/system/health')
@admin_required
def api_system_health():
    """Проверка здоровья системы"""
    try:
        # Проверка подключения к БД
        db_status = 'healthy'
        try:
            test_query = run_async(fetch_val, 'SELECT 1')
            if test_query != 1:
                db_status = 'error'
        except:
            db_status = 'error'
        
        # Получаем информацию о системе
        import psutil
        import platform
        
        memory = psutil.virtual_memory()
        
        # Информация о системе
        system_info = {
            'database': db_status,
            'memory_percent': memory.percent,
            'memory_total': round(memory.total / (1024 ** 3), 2),  # GB
            'memory_used': round(memory.used / (1024 ** 3), 2),    # GB
            'cpu_percent': psutil.cpu_percent(interval=1),
            'platform': platform.platform(),
            'python_version': platform.python_version()
        }
        
        # Время работы (заглушка)
        system_info['uptime_days'] = 1
        system_info['uptime_hours'] = 4
        
        return jsonify({
            'success': True,
            'database': db_status,
            'system': system_info
        })
    except Exception as e:
        app.logger.error(f"Error in system health check: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'database': 'error'
        }), 500

@app.route('/api/test-db')
@admin_required
def api_test_db():
    """Тест подключения к БД"""
    try:
        # Проверка подключения
        version = run_async(fetch_val, 'SELECT version()')
        
        # Проверка таблиц
        tables = run_async(fetch_query, '''
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        ''')
        
        # Количество записей
        users_count = run_async(fetch_val, 'SELECT COUNT(*) FROM users')
        subs_count = run_async(fetch_val, 'SELECT COUNT(*) FROM subscriptions')
        links_count = run_async(fetch_val, 'SELECT COUNT(*) FROM user_links')
        inst_count = run_async(fetch_val, 'SELECT COUNT(*) FROM instructions')
        
        return jsonify({
            'success': True,
            'database': {
                'version': version,
                'tables': [t['table_name'] for t in tables],
                'counts': {
                    'users': users_count,
                    'subscriptions': subs_count,
                    'links': links_count,
                    'instructions': inst_count
                }
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/export/<export_type>')
@admin_required
def api_export_data(export_type):
    """Экспорт данных"""
    try:
        if export_type == 'users':
            users = run_async(fetch_query, '''
                SELECT 
                    u.id,
                    u.telegram_id,
                    u.username,
                    u.full_name,
                    u.created_at,
                    COUNT(DISTINCT s.id) as subscriptions_count,
                    COUNT(DISTINCT ul.id) as links_count,
                    MAX(s.end_date) as last_subscription_end
                FROM users u
                LEFT JOIN subscriptions s ON u.id = s.user_id
                LEFT JOIN user_links ul ON u.id = ul.user_id
                GROUP BY u.id
                ORDER BY u.created_at DESC
            ''')
            
            # Создаем CSV
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Заголовки
            writer.writerow(['ID', 'Telegram ID', 'Username', 'Имя', 'Дата регистрации', 
                           'Кол-во подписок', 'Кол-во ссылок', 'Последняя подписка до'])
            
            # Данные
            for user in users:
                writer.writerow([
                    user['id'],
                    user['telegram_id'],
                    user['username'] or '',
                    user['full_name'] or '',
                    user['created_at'].strftime('%Y-%m-%d %H:%M:%S'),
                    user['subscriptions_count'],
                    user['links_count'],
                    user['last_subscription_end'].strftime('%Y-%m-%d') if user['last_subscription_end'] else ''
                ])
            
            response = make_response(output.getvalue())
            response.headers['Content-Disposition'] = f'attachment; filename=users_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            response.headers['Content-type'] = 'text/csv'
            return response
            
        elif export_type == 'subscriptions':
            subscriptions = run_async(fetch_query, '''
                SELECT 
                    s.id,
                    u.telegram_id,
                    u.username,
                    u.full_name,
                    s.plan,
                    s.start_date,
                    s.end_date,
                    s.is_active,
                    CASE 
                        WHEN s.end_date > CURRENT_TIMESTAMP THEN 'active'
                        ELSE 'expired'
                    END as status
                FROM subscriptions s
                JOIN users u ON s.user_id = u.id
                ORDER BY s.end_date DESC
            ''')
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            writer.writerow(['ID', 'Telegram ID', 'Username', 'Имя', 'Тариф', 'Начало', 
                           'Окончание', 'Активна', 'Статус'])
            
            for sub in subscriptions:
                writer.writerow([
                    sub['id'],
                    sub['telegram_id'],
                    sub['username'] or '',
                    sub['full_name'] or '',
                    sub['plan'] or '',
                    sub['start_date'].strftime('%Y-%m-%d %H:%M:%S'),
                    sub['end_date'].strftime('%Y-%m-%d %H:%M:%S'),
                    'Да' if sub['is_active'] else 'Нет',
                    sub['status']
                ])
            
            response = make_response(output.getvalue())
            response.headers['Content-Disposition'] = f'attachment; filename=subscriptions_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            response.headers['Content-type'] = 'text/csv'
            return response
            
        return jsonify({'success': False, 'error': 'Неизвестный тип экспорта'}), 400
        
    except Exception as e:
        app.logger.error(f"Error in export: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/backup')
@admin_required
def api_backup():
    """Создание резервной копии"""
    try:
        # Здесь можно реализовать создание резервной копии
        return jsonify({
            'success': True,
            'message': 'Резервная копия создана',
            'backup_time': datetime.now().isoformat()
        })
    except Exception as e:
        app.logger.error(f"Error in backup: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/clear-cache')
@admin_required
def api_clear_cache():
    """Очистка кэша"""
    try:
        # Здесь можно реализовать очистку кэша
        return jsonify({
            'success': True,
            'message': 'Кэш очищен'
        })
    except Exception as e:
        app.logger.error(f"Error clearing cache: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

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
                    return jsonify({'success': False, 'error': 'Сессия истекла'}), 401
            except:
                pass
        session['last_activity'] = datetime.now().isoformat()

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return jsonify({'success': False, 'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'success': False, 'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)