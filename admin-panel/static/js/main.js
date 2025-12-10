class AdminPanel {
    constructor() {
        this.currentSection = 'dashboard';
        this.init();
    }

    init() {
        this.checkAuth();
        this.setupEventListeners();
        this.loadDashboard();
    }

    async checkAuth() {
        try {
            // Проверяем авторизацию при загрузке
            // Если не авторизован, редирект на логин
            const response = await api.get('/api/stats');
            if (!response.success && response.error === 'Требуется авторизация') {
                window.location.href = '/login';
            }
        } catch (error) {
            console.error('Auth check failed:', error);
        }
    }

    setupEventListeners() {
        // Навигация
        document.querySelectorAll('.nav-item').forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                const section = item.getAttribute('href').substring(1);
                this.showSection(section);
            });
        });
    }

    showSection(sectionId) {
        // Скрываем все секции
        document.querySelectorAll('.content-section').forEach(section => {
            section.style.display = 'none';
        });

        // Убираем активный класс со всех пунктов меню
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.remove('active');
        });

        // Показываем выбранную секцию
        const section = document.getElementById(`${sectionId}-section`);
        if (section) {
            section.style.display = 'block';

            // Добавляем активный класс к выбранному пункту меню
            const navItem = document.querySelector(`.nav-item[href="#${sectionId}"]`);
            if (navItem) {
                navItem.classList.add('active');
            }

            // Загружаем данные для секции
            this.loadSectionData(sectionId);
        }

        this.currentSection = sectionId;
    }

    loadSectionData(sectionId) {
        switch (sectionId) {
            case 'dashboard':
                this.loadDashboard();
                break;
            case 'users':
                if (typeof loadUsers === 'function') loadUsers();
                break;
            case 'subscriptions':
                if (typeof loadSubscriptions === 'function') loadSubscriptions();
                break;
            case 'bot':
                this.loadBotStatus();
                break;
        }
    }

    async loadDashboard() {
        try {
            const response = await api.get('/api/stats');
            if (response.success) {
                this.updateDashboardStats(response.stats);
            }
        } catch (error) {
            console.error('Failed to load dashboard:', error);
        }
    }

    updateDashboardStats(stats) {
        if (stats.total_users !== undefined) {
            document.getElementById('total-users').textContent = stats.total_users;
        }
        if (stats.active_subs !== undefined) {
            document.getElementById('active-subs').textContent = stats.active_subs;
        }
        if (stats.today_payments_amount !== undefined) {
            document.getElementById('today-revenue').textContent = `${stats.today_payments_amount} ₽`;
        }
    }

    async loadBotStatus() {
        try {
            const response = await api.get('/api/bot/status');
            if (response.success) {
                document.getElementById('bot-status').textContent = response.status;
                document.getElementById('bot-last-active').textContent =
                    new Date(response.last_active).toLocaleString('ru-RU');

                // Обновляем цвет статуса
                const statusElement = document.getElementById('bot-status');
                statusElement.className = 'status-value ' +
                    (response.status === 'online' ? 'online' : 'offline');
            }
        } catch (error) {
            console.error('Failed to load bot status:', error);
        }
    }

    async restartBot() {
        if (confirm('Перезапустить бота?')) {
            try {
                const response = await api.post('/api/bot/restart');
                if (response.success) {
                    api.showNotification(response.message, 'success');
                    this.loadBotStatus();
                }
            } catch (error) {
                console.error('Failed to restart bot:', error);
            }
        }
    }

    async clearBotCache() {
        if (confirm('Очистить кэш бота?')) {
            // Здесь можно добавить очистку кэша
            api.showNotification('Кэш очищен', 'success');
        }
    }

    async checkBotStatus() {
        api.showNotification('Проверка статуса...', 'info');
        await this.loadBotStatus();
    }
}

// Утилиты
function formatDate(dateString) {
    if (!dateString) return '-';
    try {
        const date = new Date(dateString);
        return date.toLocaleDateString('ru-RU');
    } catch (e) {
        return dateString;
    }
}

function formatDateTime(dateString) {
    if (!dateString) return '-';
    try {
        const date = new Date(dateString);
        return date.toLocaleString('ru-RU');
    } catch (e) {
        return dateString;
    }
}

function logout() {
    if (confirm('Выйти из системы?')) {
        window.location.href = '/logout';
    }
}

// Инициализация при загрузке страницы
let adminPanel;
document.addEventListener('DOMContentLoaded', () => {
    adminPanel = new AdminPanel();

    // Экспортируем функции в глобальную область видимости
    window.showSection = (sectionId) => adminPanel.showSection(sectionId);
    window.logout = logout;
    window.restartBot = () => adminPanel.restartBot();
    window.clearBotCache = () => adminPanel.clearBotCache();
    window.checkBotStatus = () => adminPanel.checkBotStatus();
});