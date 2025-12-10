from flask import Flask
from flask_login import LoginManager
from flask_cors import CORS
from .auth import User
import os

login_manager = LoginManager()

def create_app():
    app = Flask(__name__, 
                template_folder='../templates',
                static_folder='../static')
    
    # Конфигурация
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Инициализация расширений
    login_manager.init_app(app)
    login_manager.login_view = 'main.login_page'  # Указываем функцию для страницы логина
    CORS(app)
    
    # Регистрация маршрутов
    from .routes.main import main_bp
    from .routes.users import users_bp
    from .routes.auth import auth_bp
    from .routes.subscriptions import subscriptions_bp
    from .routes.tariffs import tariffs_bp
    from .routes.payments import payments_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(users_bp, url_prefix='/api')
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(subscriptions_bp, url_prefix='/api')
    app.register_blueprint(tariffs_bp, url_prefix='/api')
    app.register_blueprint(payments_bp, url_prefix='/api')
    
    # Загрузчик пользователя для Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        if user_id == 'admin':
            return User(user_id, 'Администратор', 'Супер админ')
        return None
    
    return app