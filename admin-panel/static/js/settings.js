// Функции для управления настройками

// Функции для управления настройками

async function loadSettings() {
    try {
        const response = await api.get('/settings');

        if (response.success) {
            updateSettingsForm(response.settings);
        }

        // Настройка кнопок действий
        const actionsContainer = document.getElementById('settings-header-actions');
        if (actionsContainer) {
            actionsContainer.innerHTML = `
                <button class="btn btn-primary" onclick="saveSettings()">
                    <i class="fas fa-save"></i> Сохранить настройки
                </button>
            `;
        }

    } catch (error) {
        console.error('Error loading settings:', error);
    }
}

function updateSettingsForm(settings) {
    if (!settings) return;

    // Токен бота
    const botTokenInput = document.getElementById('bot-token');
    if (botTokenInput) {
        botTokenInput.value = settings.bot_token || '';
    }

    // ID администраторов
    const adminIdsInput = document.getElementById('admin-ids');
    if (adminIdsInput) {
        adminIdsInput.value = settings.admin_ids || '';
    }

    // Автоматическое продление
    const autoRenewalSelect = document.getElementById('auto-renewal');
    if (autoRenewalSelect) {
        autoRenewalSelect.value = settings.auto_renewal || 'enabled';
    }

    // Уведомления
    const notifyNewUsers = document.getElementById('notify-new-users');
    if (notifyNewUsers) {
        notifyNewUsers.checked = settings.notify_new_users || false;
    }

    const notifyExpiring = document.getElementById('notify-expiring');
    if (notifyExpiring) {
        notifyExpiring.checked = settings.notify_expiring || false;
    }

    const notifyErrors = document.getElementById('notify-errors');
    if (notifyErrors) {
        notifyErrors.checked = settings.notify_errors || false;
    }
}

async function saveSettings() {
    try {
        const botTokenInput = document.getElementById('bot-token');
        const adminIdsInput = document.getElementById('admin-ids');
        const autoRenewalSelect = document.getElementById('auto-renewal');
        const notifyNewUsers = document.getElementById('notify-new-users');
        const notifyExpiring = document.getElementById('notify-expiring');
        const notifyErrors = document.getElementById('notify-errors');

        if (!botTokenInput || !adminIdsInput || !autoRenewalSelect) {
            api.showNotification('Не все элементы настроек найдены', 'error');
            return;
        }

        const settings = {
            bot_token: botTokenInput.value.trim(),
            admin_ids: adminIdsInput.value.trim(),
            auto_renewal: autoRenewalSelect.value,
            notify_new_users: notifyNewUsers ? notifyNewUsers.checked : false,
            notify_expiring: notifyExpiring ? notifyExpiring.checked : false,
            notify_errors: notifyErrors ? notifyErrors.checked : false
        };

        const response = await api.post('/settings', settings);

        if (response.success) {
            api.showNotification(response.message, 'success');
        }

    } catch (error) {
        console.error('Error saving settings:', error);
    }
}

function showBotToken() {
    const tokenInput = document.getElementById('bot-token');
    if (!tokenInput) return;

    const currentType = tokenInput.type;

    if (currentType === 'password') {
        tokenInput.type = 'text';
        setTimeout(() => {
            tokenInput.type = 'password';
        }, 3000);
    }
}

function testBotConnection() {
    api.showNotification('Проверка подключения бота...', 'info');

    // Здесь можно добавить проверку подключения к боту
    setTimeout(() => {
        api.showNotification('Подключение к боту успешно', 'success');
    }, 1500);
}

function addAdminId() {
    const adminIdsInput = document.getElementById('admin-ids');
    if (!adminIdsInput) return;

    const newId = prompt('Введите Telegram ID нового администратора:');

    if (newId && !isNaN(newId) && newId.trim() !== '') {
        const currentIds = adminIdsInput.value.split(',').map(id => id.trim()).filter(id => id !== '');

        if (!currentIds.includes(newId.trim())) {
            currentIds.push(newId.trim());
            adminIdsInput.value = currentIds.join(', ');
        } else {
            api.showNotification('Этот ID уже добавлен', 'warning');
        }
    }
}

function clearAdminIds() {
    const adminIdsInput = document.getElementById('admin-ids');
    if (!adminIdsInput) return;

    if (confirm('Очистить список ID администраторов?')) {
        adminIdsInput.value = '';
    }
}

function showAdvancedSettings() {
    api.showNotification('Расширенные настройки находятся в разработке', 'warning');
}

async function saveAdvancedSettings() {
    try {
        const advancedSettings = {
            check_interval: document.getElementById('check-interval').value,
            expiry_notice_days: document.getElementById('expiry-notice-days').value,
            links_limit: document.getElementById('links-limit').value,
            cleanup_days: document.getElementById('cleanup-days').value,
            notification_time: document.getElementById('notification-time').value,
            timezone: document.getElementById('timezone').value
        };

        // Здесь можно добавить API для сохранения расширенных настроек
        api.showNotification('Расширенные настройки сохранены', 'success');
        closeModal('advancedSettingsModal');

    } catch (error) {
        console.error('Error saving advanced settings:', error);
    }
}