class ApiService {
    constructor() {
        this.baseUrl = '';
    }

    async request(method, url, data = null) {
        try {
            const config = {
                method: method,
                headers: {}
            };

            if (data) {
                if (data instanceof FormData) {
                    config.body = data;
                } else {
                    config.headers['Content-Type'] = 'application/json';
                    config.body = JSON.stringify(data);
                }
            }

            const response = await fetch(url, config);

            if (response.status === 401) {
                // Не авторизован
                window.location.href = '/login';
                return { success: false, error: 'Требуется авторизация' };
            }

            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.error || 'Ошибка сервера');
            }

            return result;
        } catch (error) {
            console.error('API Error:', error);
            this.showNotification(error.message, 'error');
            throw error;
        }
    }

    async get(url, params = {}) {
        const queryString = Object.keys(params).length
            ? '?' + new URLSearchParams(params).toString()
            : '';
        return this.request('GET', url + queryString);
    }

    async post(url, data = {}) {
        return this.request('POST', url, data);
    }

    async put(url, data = {}) {
        return this.request('PUT', url, data);
    }

    async delete(url) {
        return this.request('DELETE', url);
    }

    showNotification(message, type = 'info') {
        // Создаем уведомление
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 12px 16px;
            border-radius: 6px;
            color: white;
            z-index: 10000;
            min-width: 300px;
            max-width: 400px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            animation: slideIn 0.3s ease;
        `;

        // Цвета в зависимости от типа
        const colors = {
            success: '#10b981',
            error: '#ef4444',
            warning: '#f59e0b',
            info: '#3b82f6'
        };

        notification.style.backgroundColor = colors[type] || colors.info;

        // Иконка
        const icons = {
            success: 'fa-check-circle',
            error: 'fa-exclamation-circle',
            warning: 'fa-exclamation-triangle',
            info: 'fa-info-circle'
        };

        notification.innerHTML = `
            <div style="display: flex; align-items: center; justify-content: space-between;">
                <div style="display: flex; align-items: center; gap: 8px;">
                    <i class="fas ${icons[type] || icons.info}" style="font-size: 18px;"></i>
                    <span>${message}</span>
                </div>
                <button onclick="this.parentElement.parentElement.remove()" 
                        style="background: none; border: none; color: white; cursor: pointer; font-size: 16px;">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;

        document.body.appendChild(notification);

        // Автоматическое удаление через 5 секунд
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 5000);

        // Добавляем CSS для анимации
        if (!document.getElementById('notification-styles')) {
            const style = document.createElement('style');
            style.id = 'notification-styles';
            style.textContent = `
                @keyframes slideIn {
                    from {
                        transform: translateX(100%);
                        opacity: 0;
                    }
                    to {
                        transform: translateX(0);
                        opacity: 1;
                    }
                }
            `;
            document.head.appendChild(style);
        }
    }
}

// Создаем глобальный экземпляр API
const api = new ApiService();