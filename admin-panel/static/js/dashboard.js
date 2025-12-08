// Функции для дашборда
async function loadDashboard() {
    try {
        // Загрузка статистики
        const statsResponse = await api.get('/dashboard/stats');
        if (statsResponse.success) {
            updateDashboardStats(statsResponse.stats, statsResponse.daily_stats);
        }

        // Загрузка последней активности
        await loadRecentActivity();

        // Настройка кнопок действий
        const actionsContainer = document.getElementById('dashboard-header-actions');
        actionsContainer.innerHTML = `
            <button class="btn btn-secondary" onclick="refreshData()">
                <i class="fas fa-sync-alt"></i> Обновить
            </button>
            <button class="btn btn-primary" onclick="showDateRangeModal()">
                <i class="fas fa-calendar-alt"></i> Выбрать период
            </button>
        `;

    } catch (error) {
        console.error('Error loading dashboard:', error);
    }
}

function updateDashboardStats(stats, dailyStats) {
    // Обновление карточек статистики
    if (stats.total_users !== undefined) {
        document.getElementById('total-users').textContent = stats.total_users;
    }

    if (stats.active_subscribers !== undefined) {
        document.getElementById('active-subs').textContent = stats.active_subscribers;
    }

    if (stats.total_links !== undefined) {
        document.getElementById('total-links').textContent = stats.total_links;
    }

    if (stats.conversion_rate !== undefined) {
        document.getElementById('conversion-rate').textContent = `${stats.conversion_rate}%`;
    }

    // Построение графика
    if (dailyStats && dailyStats.length > 0) {
        buildDailyChart(dailyStats);
    }
}

function buildDailyChart(dailyStats) {
    const ctx = document.getElementById('dailyChart').getContext('2d');

    // Очистить старый график
    if (dailyChart) {
        dailyChart.destroy();
    }

    // Подготовить данные
    const labels = dailyStats.map(stat => {
        const date = new Date(stat.date);
        return date.toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' });
    });

    const usersData = dailyStats.map(stat => stat.new_users || 0);
    const subsData = dailyStats.map(stat => stat.new_subscriptions || 0);

    dailyChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Новые пользователи',
                    data: usersData,
                    borderColor: '#3b82f6',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    borderWidth: 2,
                    tension: 0.3,
                    fill: true
                },
                {
                    label: 'Новые подписки',
                    data: subsData,
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    borderWidth: 2,
                    tension: 0.3,
                    fill: true
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        color: '#94a3b8'
                    }
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    backgroundColor: '#1e293b',
                    titleColor: '#f1f5f9',
                    bodyColor: '#f1f5f9',
                    borderColor: '#475569',
                    borderWidth: 1
                }
            },
            scales: {
                x: {
                    grid: {
                        color: '#475569'
                    },
                    ticks: {
                        color: '#94a3b8'
                    }
                },
                y: {
                    beginAtZero: true,
                    grid: {
                        color: '#475569'
                    },
                    ticks: {
                        color: '#94a3b8'
                    }
                }
            }
        }
    });
}

async function loadRecentActivity() {
    try {
        const response = await api.get('/dashboard/recent-activity');
        if (response.success) {
            const activities = response.activities;
            const tbody = document.getElementById('recent-activity-body');
            tbody.innerHTML = '';

            activities.forEach(activity => {
                const statusBadge = getStatusBadge(activity.status);
                const row = `<tr>
                    <td><strong>${activity.user_name || 'Неизвестный'}</strong></td>
                    <td>${activity.action}</td>
                    <td class="text-muted">${activity.time}</td>
                    <td>${statusBadge}</td>
                </tr>`;
                tbody.innerHTML += row;
            });
        }
    } catch (error) {
        console.error('Error loading recent activity:', error);
    }
}

function getStatusBadge(status) {
    switch (status) {
        case 'success': return '<span class="badge badge-success">Успех</span>';
        case 'warning': return '<span class="badge badge-warning">Предупреждение</span>';
        case 'danger': return '<span class="badge badge-danger">Ошибка</span>';
        default: return '<span class="badge badge-info">Инфо</span>';
    }
}

function showDateRangeModal() {
    const modalHtml = `
        <div class="modal" id="dateRangeModal">
            <div class="modal-content">
                <div class="modal-header">
                    <h2>Выбор периода</h2>
                    <button class="close-btn" onclick="closeModal('dateRangeModal')">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="form-group">
                        <label class="form-label">С</label>
                        <input type="date" id="date-from" class="form-control">
                    </div>
                    <div class="form-group">
                        <label class="form-label">По</label>
                        <input type="date" id="date-to" class="form-control">
                    </div>
                </div>
                <div class="modal-footer">
                    <button class="btn btn-primary" onclick="applyDateRange()">Применить</button>
                    <button class="btn btn-secondary" onclick="closeModal('dateRangeModal')">Отмена</button>
                </div>
            </div>
        </div>
    `;

    document.body.insertAdjacentHTML('beforeend', modalHtml);
    document.getElementById('dateRangeModal').style.display = 'flex';
}

function applyDateRange() {
    // Здесь можно добавить логику применения фильтра по дате
    console.log('Date range applied');
    closeModal('dateRangeModal');
}