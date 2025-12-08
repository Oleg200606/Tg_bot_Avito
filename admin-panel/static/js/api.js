// API функции
class ApiService {
    constructor(baseUrl = '/api') {
        this.baseUrl = baseUrl;
    }

    async get(url, params = {}) {
        try {
            const response = await axios.get(`${this.baseUrl}${url}`, { params });
            return response.data;
        } catch (error) {
            this.handleError(error);
            throw error;
        }
    }

    async post(url, data = {}) {
        try {
            const response = await axios.post(`${this.baseUrl}${url}`, data);
            return response.data;
        } catch (error) {
            this.handleError(error);
            throw error;
        }
    }

    async put(url, data = {}) {
        try {
            const response = await axios.put(`${this.baseUrl}${url}`, data);
            return response.data;
        } catch (error) {
            this.handleError(error);
            throw error;
        }
    }

    async delete(url) {
        try {
            const response = await axios.delete(`${this.baseUrl}${url}`);
            return response.data;
        } catch (error) {
            this.handleError(error);
            throw error;
        }
    }

    handleError(error) {
        console.error('API Error:', error);

        let message = 'Ошибка соединения с сервером';

        if (error.response) {
            if (error.response.status === 401) {
                window.location.href = '/login';
                return;
            }

            message = error.response.data?.error || `Ошибка ${error.response.status}`;
        } else if (error.request) {
            message = 'Сервер не отвечает';
        }

        this.showNotification(message, 'error');
    }

    showNotification(message, type = 'info') {
        // Можно использовать библиотеку для уведомлений или создать свой компонент
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
                <span>${message}</span>
            </div>
            <button class="notification-close" onclick="this.parentElement.remove()">
                <i class="fas fa-times"></i>
            </button>
        `;

        document.body.appendChild(notification);

        // Автоматическое удаление
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 5000);
    }
}

// Создаем глобальный экземпляр API
const api = new ApiService();