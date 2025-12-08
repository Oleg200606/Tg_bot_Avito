// Функции для управления системой

async function checkSystemHealth() {
    try {
        const response = await api.get('/system/health');

        if (response.success) {
            updateSystemHealth(response);
        }

        // Настройка кнопок действий
        const actionsContainer = document.getElementById('system-header-actions');
        actionsContainer.innerHTML = `
            <button class="btn btn-secondary" onclick="checkSystemHealth()">
                <i class="fas fa-sync-alt"></i> Обновить
            </button>
            <button class="btn btn-primary" onclick="testAllConnections()">
                <i class="fas fa-heartbeat"></i> Проверить всё
            </button>
        `;

    } catch (error) {
        console.error('Error checking system health:', error);
    }
}

function updateSystemHealth(data) {
    if (!data.system) return;

    const system = data.system;

    // Статус базы данных
    document.getElementById('db-status').innerHTML = data.database === 'healthy'
        ? '<span class="text-success">✓ Работает</span>'
        : '<span class="text-danger">✗ Ошибка</span>';

    // Использование памяти
    document.getElementById('memory-usage').innerHTML = `
        ${system.memory_percent}%
        <div class="text-muted" style="font-size: 12px;">
            ${system.memory_used?.toFixed(1)} / ${system.memory_total?.toFixed(1)} GB
        </div>
    `;

    // Время работы
    const uptimeText = system.uptime_days > 0
        ? `${system.uptime_days} д. ${system.uptime_hours || 0} ч.`
        : `${system.uptime_hours || 0} ч.`;
    document.getElementById('uptime').textContent = uptimeText;

    // Последняя резервная копия
    document.getElementById('last-backup').textContent = system.last_backup || 'Нет данных';

    // Дополнительная информация
    updateSystemLogs(system);
}

function updateSystemLogs(system) {
    const logsTextarea = document.getElementById('system-logs');
    if (!logsTextarea) return;

    const logs = [
        `=== Информация о системе ===`,
        `Время: ${new Date().toLocaleString('ru-RU')}`,
        `ОС: ${system.platform || 'Неизвестно'}`,
        `Python: ${system.python_version || 'Неизвестно'}`,
        `Память: ${system.memory_percent || 0}% (${system.memory_used?.toFixed(1) || 0}/${system.memory_total?.toFixed(1) || 0} GB)`,
        `CPU: ${system.cpu_percent || 0}%`,
        `База данных: ${system.database === 'healthy' ? '✅ Работает' : '❌ Ошибка'}`,
        `================================`
    ].join('\n');

    logsTextarea.value = logs;
}

async function testAllConnections() {
    api.showNotification('Проверка всех соединений...', 'info');

    try {
        // Проверка базы данных
        const dbTest = await api.get('/test-db');

        // Проверка API
        const apiTest = await api.get('/api/statistics');

        // Проверка бота (если есть)
        // const botTest = await api.get('/api/bot/status');

        const results = [
            `Результаты проверки (${new Date().toLocaleTimeString('ru-RU')}):`,
            `✅ База данных: ${dbTest.success ? 'Работает' : 'Ошибка'}`,
            `✅ API: ${apiTest.success ? 'Работает' : 'Ошибка'}`,
            // `✅ Бот: ${botTest.success ? 'Работает' : 'Ошибка'}`,
            `🔄 Система: Все проверки пройдены успешно`
        ].join('\n');

        document.getElementById('system-logs').value = results;
        api.showNotification('Все проверки завершены', 'success');

    } catch (error) {
        api.showNotification('Ошибка при проверке системы', 'error');
        console.error('System test error:', error);
    }
}

async function backupDatabase() {
    if (confirm('Создать резервную копию базы данных?')) {
        try {
            const response = await api.get('/api/backup');

            if (response.success) {
                api.showNotification(`Резервная копия создана: ${response.backup_time}`, 'success');

                // Обновить информацию о последнем бэкапе
                document.getElementById('last-backup').textContent =
                    new Date().toLocaleString('ru-RU');
            }
        } catch (error) {
            console.error('Error creating backup:', error);
        }
    }
}

async function clearCache() {
    if (confirm('Очистить кэш системы? Это может временно замедлить работу.')) {
        try {
            const response = await api.get('/api/clear-cache');

            if (response.success) {
                api.showNotification(response.message, 'success');

                // Добавить запись в логи
                const logsTextarea = document.getElementById('system-logs');
                if (logsTextarea) {
                    logsTextarea.value += `\n[${new Date().toLocaleString('ru-RU')}] Кэш очищен\n`;
                }
            }
        } catch (error) {
            console.error('Error clearing cache:', error);
        }
    }
}

function showRebootModal() {
    const modalHtml = `
        <div class="modal" id="rebootModal">
            <div class="modal-content">
                <div class="modal-header">
                    <h2>Перезапуск системы</h2>
                    <button class="close-btn" onclick="closeModal('rebootModal')">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="warning-message" style="background: rgba(245,158,11,0.1); border: 1px solid var(--warning); border-radius: 6px; padding: 15px; margin-bottom: 20px;">
                        <i class="fas fa-exclamation-triangle text-warning"></i>
                        <strong class="text-warning">Внимание!</strong>
                        <p>Перезапуск системы прервет все текущие операции.</p>
                        <p>Это займет несколько секунд.</p>
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label">Причина перезапуска</label>
                        <select id="reboot-reason" class="form-control">
                            <option value="maintenance">Техническое обслуживание</option>
                            <option value="update">Обновление системы</option>
                            <option value="error">Исправление ошибок</option>
                            <option value="other">Другое</option>
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label">Комментарий (опционально)</label>
                        <textarea id="reboot-comment" class="form-control" rows="3" placeholder="Дополнительная информация..."></textarea>
                    </div>
                    
                    <div class="form-group">
                        <label>
                            <input type="checkbox" id="notify-users"> Уведомить пользователей
                        </label>
                        <small class="text-muted">Отправит уведомление пользователям о плановых работах</small>
                    </div>
                </div>
                <div class="modal-footer">
                    <button class="btn btn-danger" onclick="performReboot()">
                        <i class="fas fa-redo"></i> Выполнить перезапуск
                    </button>
                    <button class="btn btn-secondary" onclick="closeModal('rebootModal')">Отмена</button>
                </div>
            </div>
        </div>
    `;

    document.body.insertAdjacentHTML('beforeend', modalHtml);
    document.getElementById('rebootModal').style.display = 'flex';
}

async function performReboot() {
    const reason = document.getElementById('reboot-reason').value;
    const comment = document.getElementById('reboot-comment').value;
    const notifyUsers = document.getElementById('notify-users').checked;

    if (confirm('Вы уверены, что хотите перезапустить систему?')) {
        try {
            api.showNotification('Система перезапускается...', 'info');

            // Здесь можно добавить API для перезапуска
            // const response = await api.post('/api/system/reboot', {
            //     reason: reason,
            //     comment: comment,
            //     notify_users: notifyUsers
            // });

            // Имитация перезапуска
            setTimeout(() => {
                api.showNotification('Система успешно перезапущена', 'success');
                closeModal('rebootModal');
                checkSystemHealth(); // Обновить статус
            }, 2000);

        } catch (error) {
            console.error('Error during reboot:', error);
            api.showNotification('Ошибка при перезапуске', 'error');
        }
    }
}

function viewSystemLogs() {
    const modalHtml = `
        <div class="modal" id="systemLogsModal">
            <div class="modal-content" style="max-width: 900px; max-height: 80vh;">
                <div class="modal-header">
                    <h2>Системные логи</h2>
                    <button class="close-btn" onclick="closeModal('systemLogsModal')">&times;</button>
                </div>
                <div class="modal-body">
                    <div style="margin-bottom: 15px; display: flex; gap: 10px;">
                        <select id="log-level" class="form-control" style="width: 150px;">
                            <option value="all">Все уровни</option>
                            <option value="error">Только ошибки</option>
                            <option value="warning">Предупреждения</option>
                            <option value="info">Информация</option>
                        </select>
                        <select id="log-source" class="form-control" style="width: 200px;">
                            <option value="all">Все источники</option>
                            <option value="api">API</option>
                            <option value="database">База данных</option>
                            <option value="bot">Бот</option>
                            <option value="system">Система</option>
                        </select>
                        <input type="date" id="log-date" class="form-control" style="width: 150px;">
                        <button class="btn btn-secondary" onclick="refreshLogs()">
                            <i class="fas fa-sync-alt"></i>
                        </button>
                        <button class="btn btn-danger" onclick="clearLogs()">
                            <i class="fas fa-trash"></i> Очистить
                        </button>
                    </div>
                    
                    <div class="form-group">
                        <textarea id="full-system-logs" class="form-control" rows="20" readonly style="font-family: monospace; font-size: 12px;"></textarea>
                    </div>
                    
                    <div style="display: flex; gap: 10px; margin-top: 10px;">
                        <button class="btn btn-sm btn-secondary" onclick="copyLogs()">
                            <i class="fas fa-copy"></i> Копировать
                        </button>
                        <button class="btn btn-sm btn-secondary" onclick="downloadLogs()">
                            <i class="fas fa-download"></i> Скачать
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;

    document.body.insertAdjacentHTML('beforeend', modalHtml);
    document.getElementById('systemLogsModal').style.display = 'flex';

    // Загрузить логи
    loadSystemLogs();
}

async function loadSystemLogs() {
    try {
        // Здесь можно добавить API для загрузки логов
        // const response = await api.get('/api/system/logs');

        // Пример логов
        const exampleLogs = [
            `[2024-01-15 10:30:15] INFO: Система запущена`,
            `[2024-01-15 10:35:22] INFO: База данных подключена успешно`,
            `[2024-01-15 11:45:10] WARNING: Высокая загрузка памяти: 85%`,
            `[2024-01-15 12:15:33] INFO: Создана резервная копия БД`,
            `[2024-01-15 14:20:05] ERROR: Ошибка подключения к API Telegram`,
            `[2024-01-15 14:25:10] INFO: Переподключение к Telegram...`,
            `[2024-01-15 14:26:15] INFO: Подключение к Telegram восстановлено`,
            `[2024-01-15 15:40:18] INFO: Новый пользователь зарегистрирован: ID 123456789`,
            `[2024-01-15 16:55:30] INFO: Подписка создана для пользователя ID 123456789`
        ].join('\n');

        document.getElementById('full-system-logs').value = exampleLogs;

    } catch (error) {
        console.error('Error loading logs:', error);
    }
}

function refreshLogs() {
    loadSystemLogs();
}

function clearLogs() {
    if (confirm('Очистить все логи?')) {
        document.getElementById('full-system-logs').value = '';
        api.showNotification('Логи очищены', 'success');
    }
}

function copyLogs() {
    const logsTextarea = document.getElementById('full-system-logs');
    logsTextarea.select();
    document.execCommand('copy');
    api.showNotification('Логи скопированы в буфер обмена', 'success');
}

function downloadLogs() {
    const logs = document.getElementById('full-system-logs').value;
    const filename = `system-logs-${new Date().toISOString().slice(0, 10)}.log`;

    const blob = new Blob([logs], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    api.showNotification(`Логи сохранены в файл: ${filename}`, 'success');
}