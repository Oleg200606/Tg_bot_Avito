// Функции для управления подписками

async function loadSubscriptions(page = 1) {
    try {
        const filter = document.getElementById('subscription-filter')?.value || 'active';

        const response = await api.get('/subscriptions', {
            page: page,
            filter: filter
        });

        if (response.success) {
            currentSubPage = page;
            updateSubscriptionsTable(response.subscriptions);
            updateSubscriptionStats(response.stats);
            updateSubscriptionsPagination(page, response.total_pages);
        }

        // Настройка кнопок действий
        const actionsContainer = document.getElementById('subscriptions-header-actions');
        actionsContainer.innerHTML = `
            <button class="btn btn-secondary" onclick="exportData('subscriptions')">
                <i class="fas fa-download"></i> Экспорт
            </button>
            <button class="btn btn-primary" onclick="showAddSubscriptionModal()">
                <i class="fas fa-plus"></i> Добавить
            </button>
        `;

    } catch (error) {
        console.error('Error loading subscriptions:', error);
    }
}

function updateSubscriptionsTable(subscriptions) {
    const tbody = document.getElementById('subscriptions-table-body');
    tbody.innerHTML = '';

    subscriptions.forEach(sub => {
        const status = sub.status === 'active'
            ? '<span class="badge badge-success">Активна</span>'
            : '<span class="badge badge-danger">Истекла</span>';

        const daysLeft = sub.days_left > 0 ? `${sub.days_left} дн.` : 'Истекла';
        const daysLeftClass = sub.days_left > 0
            ? (sub.days_left < 7 ? 'text-warning' : 'text-success')
            : 'text-danger';

        const row = `<tr>
            <td>
                <div><strong>${sub.full_name || 'Без имени'}</strong></div>
                <div class="text-muted">@${sub.username || 'нет'}</div>
            </td>
            <td><span class="badge badge-info">${sub.plan || 'Без тарифа'}</span></td>
            <td>${formatDate(sub.start_date)}</td>
            <td>
                ${formatDate(sub.end_date)}
                <div class="${daysLeftClass}" style="font-size: 12px;">${daysLeft}</div>
            </td>
            <td>${status}</td>
            <td>
                <button class="btn btn-sm btn-success" onclick="extendSubscription(${sub.id}, ${sub.user_id})" title="Продлить">
                    <i class="fas fa-plus"></i>
                </button>
                <button class="btn btn-sm btn-warning" onclick="editSubscription(${sub.id})" title="Редактировать">
                    <i class="fas fa-edit"></i>
                </button>
                <button class="btn btn-sm btn-danger" onclick="cancelSubscription(${sub.id})" title="Отменить">
                    <i class="fas fa-times"></i>
                </button>
            </td>
        </tr>`;

        tbody.innerHTML += row;
    });
}

function updateSubscriptionStats(stats) {
    if (!stats) return;

    if (stats.total_subscriptions !== undefined) {
        document.getElementById('total-subscriptions').textContent = stats.total_subscriptions;
    }

    if (stats.active_subscriptions !== undefined) {
        document.getElementById('active-subscriptions').textContent = stats.active_subscriptions;
    }

    if (stats.expired_subscriptions !== undefined) {
        document.getElementById('expired-subscriptions').textContent = stats.expired_subscriptions;
    }

    if (stats.avg_duration !== undefined) {
        document.getElementById('avg-duration').textContent = `${Math.round(stats.avg_duration)} дн.`;
    }
}

function updateSubscriptionsPagination(currentPage, totalPages) {
    const pagination = document.getElementById('subscriptions-pagination');
    pagination.innerHTML = '';

    if (totalPages <= 1) return;

    // Предыдущая страница
    if (currentPage > 1) {
        const prevBtn = document.createElement('button');
        prevBtn.className = 'btn btn-secondary btn-sm';
        prevBtn.innerHTML = '<i class="fas fa-chevron-left"></i>';
        prevBtn.onclick = () => loadSubscriptions(currentPage - 1);
        pagination.appendChild(prevBtn);
    }

    // Страницы
    const startPage = Math.max(1, currentPage - 2);
    const endPage = Math.min(totalPages, currentPage + 2);

    for (let i = startPage; i <= endPage; i++) {
        const pageBtn = document.createElement('button');
        pageBtn.className = `btn btn-sm ${i === currentPage ? 'btn-primary' : 'btn-secondary'}`;
        pageBtn.textContent = i;
        pageBtn.onclick = () => loadSubscriptions(i);
        pagination.appendChild(pageBtn);
    }

    // Следующая страница
    if (currentPage < totalPages) {
        const nextBtn = document.createElement('button');
        nextBtn.className = 'btn btn-secondary btn-sm';
        nextBtn.innerHTML = '<i class="fas fa-chevron-right"></i>';
        nextBtn.onclick = () => loadSubscriptions(currentPage + 1);
        pagination.appendChild(nextBtn);
    }
}

async function extendSubscription(subId, userId) {
    const days = prompt('На сколько дней продлить подписку?', '30');
    if (!days || isNaN(days) || parseInt(days) <= 0) {
        api.showNotification('Введите корректное количество дней', 'error');
        return;
    }

    try {
        const response = await api.post(`/user/${userId}/subscription`, {
            action: 'extend',
            days: parseInt(days)
        });

        if (response.success) {
            api.showNotification(response.message, 'success');
            loadSubscriptions(currentSubPage);
        }
    } catch (error) {
        console.error('Error extending subscription:', error);
    }
}

function editSubscription(subId) {
    showEditSubscriptionModal(subId);
}

async function cancelSubscription(subId) {
    if (confirm('Вы уверены, что хотите отменить подписку? Эту операцию нельзя отменить.')) {
        try {
            // Здесь можно добавить API для отмены подписки
            api.showNotification('Функция отмены подписки находится в разработке', 'warning');
            // loadSubscriptions(currentSubPage);
        } catch (error) {
            console.error('Error canceling subscription:', error);
        }
    }
}

function showAddSubscriptionModal() {
    const modalHtml = `
        <div class="modal" id="addSubscriptionModal">
            <div class="modal-content">
                <div class="modal-header">
                    <h2>Добавить подписку</h2>
                    <button class="close-btn" onclick="closeModal('addSubscriptionModal')">&times;</button>
                </div>
                <div class="modal-body">
                    <form id="addSubscriptionForm">
                        <div class="form-group">
                            <label class="form-label">Пользователь</label>
                            <select id="subscription-user" class="form-control" required>
                                <option value="">Выберите пользователя...</option>
                                <!-- Будет заполнено через JS -->
                            </select>
                        </div>
                        <div class="form-group">
                            <label class="form-label">Тариф</label>
                            <select id="subscription-plan" class="form-control" required>
                                <option value="Месячный">Месячный</option>
                                <option value="Квартальный">Квартальный</option>
                                <option value="Годовой">Годовой</option>
                                <option value="Пробный">Пробный</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label class="form-label">Длительность (дни)</label>
                            <input type="number" id="subscription-days" class="form-control" value="30" min="1" max="365" required>
                        </div>
                        <div class="form-group">
                            <label class="form-label">Дата начала</label>
                            <input type="date" id="subscription-start-date" class="form-control" value="${new Date().toISOString().split('T')[0]}">
                        </div>
                        <div class="form-group">
                            <label class="form-label">Комментарий</label>
                            <textarea id="subscription-notes" class="form-control" rows="3" placeholder="Дополнительная информация..."></textarea>
                        </div>
                    </form>
                </div>
                <div class="modal-footer">
                    <button class="btn btn-primary" onclick="saveSubscription()">Сохранить</button>
                    <button class="btn btn-secondary" onclick="closeModal('addSubscriptionModal')">Отмена</button>
                </div>
            </div>
        </div>
    `;

    document.body.insertAdjacentHTML('beforeend', modalHtml);
    document.getElementById('addSubscriptionModal').style.display = 'flex';

    // Загрузить список пользователей
    loadUsersForSubscription();
}

async function loadUsersForSubscription() {
    try {
        const response = await api.get('/users', { limit: 100 });
        if (response.success && response.users.length > 0) {
            const select = document.getElementById('subscription-user');
            select.innerHTML = '<option value="">Выберите пользователя...</option>';

            response.users.forEach(user => {
                const option = document.createElement('option');
                option.value = user.id;
                option.textContent = `${user.full_name || 'Без имени'} (@${user.username || 'нет'}) - ID: ${user.id}`;
                select.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Error loading users for subscription:', error);
    }
}

async function saveSubscription() {
    try {
        const userId = document.getElementById('subscription-user').value;
        const plan = document.getElementById('subscription-plan').value;
        const days = document.getElementById('subscription-days').value;
        const startDate = document.getElementById('subscription-start-date').value;
        const notes = document.getElementById('subscription-notes').value;

        if (!userId || !plan || !days) {
            api.showNotification('Заполните обязательные поля', 'error');
            return;
        }

        // Здесь можно добавить API для сохранения подписки
        api.showNotification('Функция добавления подписки находится в разработке', 'warning');
        closeModal('addSubscriptionModal');

    } catch (error) {
        console.error('Error saving subscription:', error);
    }
}

function showEditSubscriptionModal(subId) {
    // Реализация редактирования подписки
    api.showNotification('Функция редактирования подписки находится в разработке', 'warning');
}

// Вспомогательная функция для форматирования даты
function formatDate(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleDateString('ru-RU');
}