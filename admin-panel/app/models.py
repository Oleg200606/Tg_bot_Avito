from datetime import datetime

class User:
    def __init__(self, id, telegram_id, username=None, full_name=None, 
                 created_at=None, is_admin=False):
        self.id = id
        self.telegram_id = telegram_id
        self.username = username
        self.full_name = full_name
        self.created_at = created_at or datetime.now()
        self.is_admin = is_admin
    
    @staticmethod
    def get_all(limit=20, offset=0, search=None, filter_type='all'):
        """Получить всех пользователей"""
        query = """
            SELECT u.*,
                   COUNT(DISTINCT ul.id) as links_count,
                   COUNT(DISTINCT s.id) as subscriptions_count,
                   MAX(s.end_date) as subscription_end,
                   BOOL_OR(s.is_active AND s.end_date > NOW()) as has_active_sub
            FROM users u
            LEFT JOIN user_links ul ON u.id = ul.user_id
            LEFT JOIN subscriptions s ON u.id = s.user_id
        """
        
        where_clauses = []
        params = []
        
        if search:
            where_clauses.append("""
                (u.telegram_id::text LIKE %s OR 
                 u.username ILIKE %s OR 
                 u.full_name ILIKE %s)
            """)
            search_param = f"%{search}%"
            params.extend([search_param, search_param, search_param])
        
        if filter_type == 'active':
            where_clauses.append("s.is_active = TRUE AND s.end_date > NOW()")
        elif filter_type == 'inactive':
            where_clauses.append("(s.is_active = FALSE OR s.id IS NULL)")
        
        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)
        
        query += """
            GROUP BY u.id
            ORDER BY u.created_at DESC
            LIMIT %s OFFSET %s
        """
        
        params.extend([limit, offset])
        
        return query, params
    
    @staticmethod
    def get_by_id(user_id):
        """Получить пользователя по ID"""
        query = """
            SELECT u.*,
                   COUNT(DISTINCT ul.id) as links_count,
                   COUNT(DISTINCT s.id) as subscriptions_count,
                   COUNT(DISTINCT p.id) as payments_count,
                   COALESCE(SUM(CASE WHEN p.status = 'succeeded' THEN p.amount ELSE 0 END), 0) as total_spent
            FROM users u
            LEFT JOIN user_links ul ON u.id = ul.user_id
            LEFT JOIN subscriptions s ON u.id = s.user_id
            LEFT JOIN payments p ON u.id = p.user_id
            WHERE u.id = %s
            GROUP BY u.id
        """
        return query, [user_id]
    
    @staticmethod
    def get_subscriptions(user_id):
        """Получить подписки пользователя"""
        query = """
            SELECT s.*,
                   tp.name as tariff_name,
                   tp.request_limit as tariff_limit
            FROM subscriptions s
            LEFT JOIN tariff_plans tp ON s.plan = tp.name
            WHERE s.user_id = %s
            ORDER BY s.created_at DESC
            LIMIT 10
        """
        return query, [user_id]
    
    @staticmethod
    def get_payments(user_id):
        """Получить платежи пользователя"""
        query = """
            SELECT p.*,
                   tp.name as tariff_name
            FROM payments p
            LEFT JOIN tariff_plans tp ON p.tariff_plan_id = tp.id
            WHERE p.user_id = %s
            ORDER BY p.created_at DESC
            LIMIT 10
        """
        return query, [user_id]

class Subscription:
    @staticmethod
    def get_all(limit=20, offset=0, filter_type='all', search=None):
        """Получить все подписки"""
        query = """
            SELECT s.*,
                   u.full_name,
                   u.username,
                   u.telegram_id,
                   EXTRACT(DAY FROM (s.end_date - NOW())) as days_left,
                   tp.name as tariff_name,
                   tp.request_limit as tariff_limit
            FROM subscriptions s
            LEFT JOIN users u ON s.user_id = u.id
            LEFT JOIN tariff_plans tp ON s.plan = tp.name
        """
        
        where_clauses = []
        params = []
        
        if filter_type == 'active':
            where_clauses.append("s.is_active = TRUE AND s.end_date > NOW()")
        elif filter_type == 'expired':
            where_clauses.append("s.is_active = FALSE OR s.end_date <= NOW()")
        elif filter_type == 'trial':
            where_clauses.append("s.plan = 'Пробный'")
        
        if search:
            where_clauses.append("""
                (u.telegram_id::text LIKE %s OR 
                 u.username ILIKE %s OR 
                 u.full_name ILIKE %s OR
                 s.plan ILIKE %s)
            """)
            search_param = f"%{search}%"
            params.extend([search_param, search_param, search_param, search_param])
        
        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)
        
        query += " ORDER BY s.end_date DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        
        return query, params
    
    @staticmethod
    def get_stats():
        """Статистика по подпискам"""
        query = """
            SELECT 
                COUNT(*) as total_subscriptions,
                COUNT(CASE WHEN is_active = TRUE AND end_date > NOW() THEN 1 END) as active_subscriptions,
                COUNT(CASE WHEN is_active = FALSE OR end_date <= NOW() THEN 1 END) as expired_subscriptions,
                AVG(EXTRACT(DAY FROM (end_date - start_date))) as avg_duration,
                SUM(request_limit - used_requests) as total_requests_available,
                SUM(used_requests) as total_requests_used
            FROM subscriptions
        """
        return query, []
    
    @staticmethod
    def get_by_id(subscription_id):
        """Получить подписку по ID"""
        query = """
            SELECT s.*,
                   u.full_name,
                   u.username,
                   u.telegram_id,
                   tp.name as tariff_name,
                   tp.request_limit as tariff_limit
            FROM subscriptions s
            LEFT JOIN users u ON s.user_id = u.id
            LEFT JOIN tariff_plans tp ON s.plan = tp.name
            WHERE s.id = %s
        """
        return query, [subscription_id]
    
    @staticmethod
    def create(user_id, plan, days, request_limit, notes=None):
        """Создать новую подписку"""
        start_date = datetime.now()
        end_date = start_date + timedelta(days=days)
        
        query = """
            INSERT INTO subscriptions 
            (user_id, plan, start_date, end_date, is_active, request_limit, notes)
            VALUES (%s, %s, %s, %s, TRUE, %s, %s)
            RETURNING *
        """
        params = [user_id, plan, start_date, end_date, request_limit, notes]
        return query, params
    
    @staticmethod
    def update(subscription_id, **kwargs):
        """Обновить подписку"""
        if not kwargs:
            return None, []
        
        updates = []
        params = []
        for key, value in kwargs.items():
            if value is not None:
                updates.append(f"{key} = %s")
                params.append(value)
        
        query = f"UPDATE subscriptions SET {', '.join(updates)} WHERE id = %s"
        params.append(subscription_id)
        
        return query, params
    
    @staticmethod
    def extend(subscription_id, days):
        """Продлить подписку на указанное количество дней"""
        query = """
            UPDATE subscriptions 
            SET end_date = end_date + INTERVAL '%s days',
                is_active = TRUE,
                updated_at = NOW()
            WHERE id = %s
        """
        return query, [days, subscription_id]
    
    @staticmethod
    def cancel(subscription_id):
        """Отменить подписку"""
        query = "UPDATE subscriptions SET is_active = FALSE, updated_at = NOW() WHERE id = %s"
        return query, [subscription_id]
    
    @staticmethod
    def reset_requests(subscription_id):
        """Сбросить счетчик использованных запросов"""
        query = "UPDATE subscriptions SET used_requests = 0, updated_at = NOW() WHERE id = %s"
        return query, [subscription_id]

# Класс для тарифных планов
class TariffPlan:
    @staticmethod
    def get_all():
        """Получить все тарифные планы"""
        query = "SELECT * FROM tariff_plans ORDER BY price ASC"
        return query, []
    
    @staticmethod
    def get_by_id(plan_id):
        """Получить тариф по ID"""
        query = "SELECT * FROM tariff_plans WHERE id = %s"
        return query, [plan_id]
    
    @staticmethod
    def create(name, price, duration_days, request_limit, description=None, is_active=True):
        """Создать новый тарифный план"""
        query = """
            INSERT INTO tariff_plans 
            (name, price, duration_days, request_limit, description, is_active)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING *
        """
        params = [name, price, duration_days, request_limit, description, is_active]
        return query, params
    
    @staticmethod
    def update(plan_id, **kwargs):
        """Обновить тарифный план"""
        if not kwargs:
            return None, []
        
        updates = []
        params = []
        for key, value in kwargs.items():
            if value is not None:
                updates.append(f"{key} = %s")
                params.append(value)
        
        query = f"UPDATE tariff_plans SET {', '.join(updates)} WHERE id = %s"
        params.append(plan_id)
        
        return query, params
    
    @staticmethod
    def delete(plan_id):
        """Удалить тарифный план"""
        query = "DELETE FROM tariff_plans WHERE id = %s"
        return query, [plan_id]