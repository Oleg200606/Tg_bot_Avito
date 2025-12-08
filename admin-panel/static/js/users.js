// Функции для управления пользователями
let searchTimer = null;

async function loadUsers(page = 1) {
    try {
        const search = document.getElementById('user-search')?.value || '';
        const filter = document.getElementById('user-filter')?.value || '';

        const params = {
            page: page,
            limit: 20,
            search: search,
            filter: filter
        };

        const response = await api.get('/users', params);

        if (response.success) {
            currentUserPage = page;
            updateUsersTable(response.users);
            updateUsersPagination(page, response.total_pages);
            document.getElementById('users-count').textContent = `Найдено: ${response.total}`;
        }

        // Настройка кнопок действий
        const actionsContainer = document.getElementById('users-header-actions');
        actionsContainer.innerHTML = `
            <button class="btn btn-secondary" onclick="exportData('users')">
                <i class="fas fa-download"></i> Экспорт
            </button>
            <button class="btn btn-primary" onclick="showAddUserModal()">
                <i class="fas fa-plus"></i> Добавить
            </button>
        `;

    } catch (error) {
        console.error('Error loading users:', error);
    }
}

function updateUsersTable(users) {
    const tbody = document.getElementById('users-table-body');
    tbody.innerHTML = '';

    users.forEach(user => {
        const subscriptionStatus = user.has_active_sub
            ? '<span class="badge badge-success">Активна</span>'
            : '<span class="badge badge-danger">Нет</span>';

        const subscriptionEnd = user.subscription_end
            ? new Date(user.subscription_end).toLocaleDateString('ru-RU')
            : '-';

        const adminBadge = user.is_admin ? '<span class="badge badge-info">Админ</span> ' : '';

        const row = `<tr>
            <td><strong>${user.id}</strong></td>
            <td>
                ${adminBadge}
                <div><strong>${user.full_name || 'Без имени'}</strong></div>
                <div class="text-muted">@${user.username || 'без username'}</div>
            </td>
            <td><code>${user.telegram_id}</code></td>
            <td>${new Date(user.created_at).toLocaleDateString('ru-RU')}</td>
            <td>
                ${subscriptionStatus}
                <div class="text-muted" style="font-size: 12px;">${subscriptionEnd}</div>
            </td>
            <td><strong>${user.links_count || 0}</strong></td>
            <td>
                <button class="btn btn-sm btn-secondary" onclick="viewUserDetails(${user.id})" title="Просмотр">
                    <i class="fas fa-eye"></i>
                </button>
                <button class="btn btn-sm btn-primary" onclick="editUser(${user.id})" title="Редактировать">
                    <i class="fas fa-edit"></i>
                </button>
                <button class="btn btn-sm btn-danger" onclick="deleteUser(${user.id})" title="Удалить">
                    <i class="fas fa-trash"></i>
                </button>
            </td>
        </tr>`;

        tbody.innerHTML += row;
    });
}

function updateUsersPagination(currentPage, totalPages) {
    const pagination = document.getElementById('users-pagination');
    pagination.innerHTML = '';

    if (totalPages <= 1) return;

    // Предыдущая страница
    if (currentPage > 1) {
        const prevBtn = document.createElement('button');
        prevBtn.className = 'btn btn-secondary btn-sm';
        prevBtn.innerHTML = '<i class="fas fa-chevron-left"></i>';
        prevBtn.onclick = () => loadUsers(currentPage - 1);
        pagination.appendChild(prevBtn);
    }

    // Страницы
    const startPage = Math.max(1, currentPage - 2);
    const endPage = Math.min(totalPages, currentPage + 2);

    for (let i = startPage; i <= endPage; i++) {
        const pageBtn = document.createElement('button');
        pageBtn.className = `btn btn-sm ${i === currentPage ? 'btn-primary' : 'btn-secondary'}`;
        pageBtn.textContent = i;
        pageBtn.onclick = () => loadUsers(i);
        pagination.appendChild(pageBtn);
    }

    // Следующая страница
    if (currentPage < totalPages) {
        const nextBtn = document.createElement('button');
        nextBtn.className = 'btn btn-secondary btn-sm';
        nextBtn.innerHTML = '<i class="fas fa-chevron-right"></i>';
        nextBtn.onclick = () => loadUsers(currentPage + 1);
        pagination.appendChild(nextBtn);
    }
}

// Дебаунс для поиска
function debounce(func, wait) {
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(searchTimer);
            func(...args);
        };
        clearTimeout(searchTimer);
        searchTimer = setTimeout(later, wait);
    };
}

const debouncedSearch = debounce(() => {
    loadUsers(1);
}, 500);

// Просмотр деталей пользователя
async function viewUserDetails(userId) {
    try {
        const response = await api.get(`/user/${userId}`);
        if (response.success) {
            showUserDetailsModal(response.user, response.subscriptions, response.links);
        }
    } catch (error) {
        console.error('Error loading user details:', error);
    }
}

function showUserDetailsModal(user, subscriptions, links) {
    const modalHtml = `
        <div class="modal" id="userDetailsModal">
            <div class="modal-content">
                <div class="modal-header">
                    <h2>Детали пользователя</h2>
                    <button class="close-btn" onclick="closeModal('userDetailsModal')">&times;</button>
                </div>
                <div class="modal-body">
                    <div style="margin-bottom: 20px;">
                        <h3>${user.full_name || 'Без имени'}</h3>
                        <p><strong>Telegram ID:</strong> <code>${user.telegram_id}</code></p>
                        <p><strong>Username:</strong> @${user.username || 'нет'}</p>
                        <p><strong>Зарегистрирован:</strong> ${new Date(user.created_at).toLocaleString('ru-RU')}</p>
                        <p><strong>Админ:</strong> ${user.is_admin ? 'Да' : 'Нет'}</p>
                    </div>
                    
                    <div style="margin-bottom: 20px;">
                        <h4>Подписки (${subscriptions.length})</h4>
                        ${subscriptions.map(sub => `
                            <div style="background: rgba(255,255,255,0.05); padding: 10px; border-radius: 6px; margin-bottom: 5px;">
                                <strong>${sub.plan || 'Без названия'}</strong> - 
                                ${new Date(sub.start_date).toLocaleDateString('ru-RU')} до 
                                ${new Date(sub.end_date).toLocaleDateString('ru-RU')}
                                <span class="badge ${sub.status === 'active' ? 'badge-success' : 'badge-danger'}">
                                    ${sub.status === 'active' ? 'Активна' : 'Неактивна'}
                                </span>
                            </div>
                        `).join('')}
                    </div>
                    
                    <div>
                        <h4>Ссылки (${links.length})</h4>
                        ${links.map(link => `
                            <div style="background: rgba(255,255,255,0.05); padding: 10px; border-radius: 6px; margin-bottom: 5px; font-size: 12px;">
                                <a href="${link.link}" target="_blank">${link.link.substring(0, 60)}...</a>
                                <div class="text-muted">${new Date(link.created_at).toLocaleString('ru-RU')}</div>
                            </div>
                        `).join('')}
                    </div>
                </div>
                <div class="modal-footer">
                    <button class="btn btn-primary" onclick="editUser(${user.id})">Редактировать</button>
                    <button class="btn btn-secondary" onclick="closeModal('userDetailsModal')">Закрыть</button>
                </div>
            </div>
        </div>
    `;

    document.body.insertAdjacentHTML('beforeend', modalHtml);
    document.getElementById('userDetailsModal').style.display = 'flex';
}

function editUser(userId) {
    showEditUserModal(userId);
}

async function deleteUser(userId) {
    if (confirm(`Вы уверены, что хотите удалить пользователя #${userId}?`)) {
        try {
            // Здесь можно добавить API для удаления пользователя
            api.showNotification('Функция удаления пользователя находится в разработке', 'warning');
            // loadUsers(currentUserPage);
        } catch (error) {
            console.error('Error deleting user:', error);
        }
    }
}

function showAddUserModal() {
    const modalHtml = `
        <div class="modal" id="addUserModal">
            <div class="modal-content">
                <div class="modal-header">
                    <h2>Добавить пользователя</h2>
                    <button class="close-btn" onclick="closeModal('addUserModal')">&times;</button>
                </div>
                <div class="modal-body">
                    <form id="addUserForm">
                        <div class="form-group">
                            <label class="form-label">Telegram ID</label>
                            <input type="number" id="user-telegram-id" class="form-control" required>
                        </div>
                        <div class="form-group">
                            <label class="form-label">Имя</label>
                            <input type="text" id="user-full-name" class="form-control">
                        </div>
                        <div class="form-group">
                            <label class="form-label">Username</label>
                            <input type="text" id="user-username" class="form-control">
                        </div>
                        <div class="form-group">
                            <label class="form-label">Создать подписку</label>
                            <select id="user-subscription" class="form-control">
                                <option value="">Нет</option>
                                <option value="30">30 дней</option>
                                <option value="90">90 дней</option>
                                <option value="365">365 дней</option>
                            </select>
                        </div>
                    </form>
                </div>
                <div class="modal-footer">
                    <button class="btn btn-primary" onclick="saveUser()">Сохранить</button>
                    <button class="btn btn-secondary" onclick="closeModal('addUserModal')">Отмена</button>
                </div>
            </div>
        </div>
    `;

    document.body.insertAdjacentHTML('beforeend', modalHtml);
    document.getElementById('addUserModal').style.display = 'flex';
}

async function saveUser() {
    try {
        const telegramId = document.getElementById('user-telegram-id').value;
        const fullName = document.getElementById('user-full-name').value;
        const username = document.getElementById('user-username').value;
        const subscriptionDays = document.getElementById('user-subscription').value;

        if (!telegramId) {
            api.showNotification('Telegram ID обязателен', 'error');
            return;
        }

        // Здесь можно добавить API для сохранения пользователя
        api.showNotification('Функция добавления пользователя находится в разработке', 'warning');
        closeModal('addUserModal');

    } catch (error) {
        console.error('Error saving user:', error);
    }
}

function exportData(type) {
    window.location.href = `/api/export/${type}`;
}