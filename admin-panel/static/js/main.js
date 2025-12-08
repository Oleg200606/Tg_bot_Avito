// Конфигурация
const API_BASE = '/api';
let currentSection = 'dashboard';
let currentUserPage = 1;
let currentSubPage = 1;
let dailyChart = null;

// Основные функции навигации
function showSection(section) {
    // Скрыть все секции
    document.querySelectorAll('[id$="-section"]').forEach(el => {
        el.style.display = 'none';
    });

    // Показать выбранную секцию
    document.getElementById(section + '-section').style.display = 'block';

    // Обновить активный пункт меню
    document.querySelectorAll('.nav-item').forEach(el => {
        el.classList.remove('active');
    });

    document.querySelector(`.nav-item[onclick="showSection('${section}')"]`).classList.add('active');

    currentSection = section;

    // Загрузить данные для секции
    switch (section) {
        case 'dashboard':
            loadDashboard();
            break;
        case 'users':
            loadUsers();
            break;
        case 'subscriptions':
            loadSubscriptions();
            break;
        case 'instructions':
            loadInstructions();
            break;
        case 'settings':
            loadSettings();
            break;
        case 'system':
            checkSystemHealth();
            break;
    }
}

// Выход из системы
// Выход из системы
async function logout() {
    if (confirm('Вы уверены, что хотите выйти?')) {
        try {
            const response = await axios.post('/logout');
            if (response.data.success) {
                window.location.href = response.data.redirect || '/login';
            }
        } catch (error) {
            console.error('Logout error:', error);
            // Если POST не работает, попробуем GET
            window.location.href = '/logout';
        }
    }
}

// Обновление данных
function refreshData() {
    switch (currentSection) {
        case 'dashboard':
            loadDashboard();
            break;
        case 'users':
            loadUsers(currentUserPage);
            break;
        case 'subscriptions':
            loadSubscriptions(currentSubPage);
            break;
        case 'instructions':
            loadInstructions();
            break;
        case 'system':
            checkSystemHealth();
            break;
    }
}

// Закрытие модальных окон
function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'none';
        setTimeout(() => modal.remove(), 300);
    }
}

// Инициализация
document.addEventListener('DOMContentLoaded', function () {
    // Проверка авторизации
    checkAuth();

    // Загрузить дашборд при старте
    loadDashboard();
});

// Проверка авторизации
async function checkAuth() {
    try {
        const response = await axios.get('/api/admin/current');
        if (response.data.success) {
            const admin = response.data.admin;
            document.getElementById('admin-name').textContent = admin.name;
            document.getElementById('admin-role').textContent = admin.role;
        }
    } catch (error) {
        console.error('Auth check failed:', error);
        if (error.response && error.response.status === 401) {
            window.location.href = '/login';
        }
    }
}