let currentPage = 1;
let totalPages = 1;

async function loadUsers(page = 1) {
    try {
        currentPage = page;

        const search = document.getElementById('user-search')?.value || '';
        const params = {
            page: page,
            limit: 20
        };

        if (search) {
            // Поиск будет обрабатываться на сервере
            // Пока просто перезагружаем список
        }

        const response = await api.get('/api/users', params);

        if (response.success) {
            updateUsersTable(response.users);
            updatePagination(page, response.total_pages);
        }
    } catch (error) {
        console.error('Error loading users:', error);
    }
}

function updateUsersTable(users) {
    const tbody = document.getElementById('users-table-body');
    tbody.innerHTML = '';

    if (users.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="5" class="text-center">Нет пользователей</td>
            </tr>
        `;
        return;
    }

    users.forEach(user => {
        const row = document.createElement('tr');

        let subscriptionInfo = '<span class="badge badge-secondary">Нет подписки</span>';
        if (user.subscription && user.subscription.active) {
            const endDate = new Date(user.subscription.end);
            const daysLeft = Math.ceil((endDate - new Date()) / (1000 * 60 * 60 * 24));

            subscriptionInfo = `
                <div>
                    <span class="badge badge-success">Активна</span>
                    <div style="font-size: 12px; color: #94a3b8; margin-top: 4px;">
                        ${user.subscription.plan} | до: ${formatDate(user.subscription.end)}
                    </div>
                </div>
            `;
        }

        row.innerHTML = `
            <td><strong>${user.id}</strong></td>
            <td>
                <div><strong>${user.full_name || 'Без имени'}</strong></div>
                <div style="font-size: 12px; color: #94a3b8;">@${user.username || 'без username'}</div>
            </td>
            <td><code>${user.telegram_id}</code></td>
            <td>${subscriptionInfo}</td>
            <td>
                <button class="btn btn-sm btn-secondary" onclick="viewUserDetails(${user.id})">
                    <i class="fas fa-eye"></i>
                </button>
                <button class="btn btn-sm btn-primary" onclick="manageUserSubscription(${user.id})">
                    <i class="fas fa-crown"></i>
                </button>
            </td>
        `;

        tbody.appendChild(row);
    });
}

function updatePagination(page, total) {
    const pagination = document.getElementById('users-pagination');
    pagination.innerHTML = '';

    totalPages = total;

    if (totalPages <= 1) return;

    // Предыдущая страница
    if (page > 1) {
        const prevBtn = document.createElement('button');
        prevBtn.innerHTML = '<i class="fas fa-chevron-left"></i>';
        prevBtn.onclick = () => loadUsers(page - 1);
        pagination.appendChild(prevBtn);
    }

    // Страницы
    const startPage = Math.max(1, page - 2);
    const endPage = Math.min(totalPages, page + 2);

    for (let i = startPage; i <= endPage; i++) {
        const pageBtn = document.createElement('button');
        pageBtn.textContent = i;
        if (i === page) {
            pageBtn.classList.add('active');
        }
        pageBtn.onclick = () => loadUsers(i);
        pagination.appendChild(pageBtn);
    }

    // Следующая страница
    if (page < totalPages) {
        const nextBtn = document.createElement('button');
        nextBtn.innerHTML = '<i class="fas fa-chevron-right"></i>';
        nextBtn.onclick = () => loadUsers(page + 1);
        pagination.appendChild(nextBtn);
    }
}

async function viewUserDetails(userId) {
    try {
        const response = await api.get(`/api/user/${userId}`);
        if (response.success) {
            showUserDetailsModal(response);
        }
    } catch (error) {
        console.error('Error loading user details:', error);
    }
}

async function manageUserSubscription(userId) {
    try {
        const response = await api.get(`/api/user/${userId}`);
        if (response.success) {
            showManageSubscriptionModal(response);
        }
    } catch (error) {
        console.error('Error loading user for subscription:', error);
    }
}

function showUserDetailsModal(data) {
    const modalHtml = `
        <div class="modal">
            <div class="modal-content">
                <div class="modal-header">
                    <h2>Детали пользователя</h2>
                    <button class="close-btn" onclick="closeModal()">&times;</button>
                </div>
                <div class="modal-body">
                    <div style="margin-bottom: 20px;">
                        <h3>${data.user.full_name || 'Без имени'}</h3>
                        <p><strong>Telegram ID:</strong> <code>${data.user.telegram_id}</code></p>
                        <p><strong>Username:</strong> @${data.user.username || 'нет'}</p>
                        <p><strong>Зарегистрирован:</strong> ${formatDateTime(data.user.created_at)}</p>
                    </div>
                    
                    ${data.user.subscription ? `
                    <div style="background: rgba(16,185,129,0.1); padding: 15px; border-radius: 8px; margin-bottom: 20px;">
                        <h4>Текущая подписка</h4>
                        <p><strong>Тариф:</strong> ${data.user.subscription.plan}</p>
                        <p><strong>Начало:</strong> ${formatDate(data.user.subscription.start_date)}</p>
                        <p><strong>Окончание:</strong> ${formatDate(data.user.subscription.end_date)}</p>
                        <p><strong>Статус:</strong> ${data.user.subscription.is_active ? 'Активна' : 'Неактивна'}</p>
                        <p><strong>Лимит запросов:</strong> ${data.user.subscription.used_requests || 0}/${data.user.subscription.request_limit || 0}</p>
                    </div>
                    ` : ''}
                    
                    <div style="display: flex; gap: 20px;">
                        <div style="flex: 1;">
                            <h5>История подписок</h5>
                            ${data.subscription_history.map(sub => `
                                <div style="background: rgba(255,255,255,0.05); padding: 10px; border-radius: 6px; margin-bottom: 5px; font-size: 12px;">
                                    <strong>${sub.plan}</strong><br>
                                    ${formatDate(sub.start_date)} - ${formatDate(sub.end_date)}
                                    <div style="color: ${sub.is_active ? '#10b981' : '#94a3b8'}">
                                        ${sub.is_active ? 'Активна' : 'Завершена'}
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                        
                        <div style="flex: 1;">
                            <h5>Платежи</h5>
                            ${data.payments.map(payment => `
                                <div style="background: rgba(255,255,255,0.05); padding: 10px; border-radius: 6px; margin-bottom: 5px; font-size: 12px;">
                                    <strong>${payment.amount} ₽</strong><br>
                                    ${formatDate(payment.created_at)}
                                    <div class="badge ${payment.status === 'succeeded' ? 'badge-success' : 'badge-danger'}">
                                        ${payment.status}
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                </div>
                <div class="modal-footer">
                    <button class="btn btn-secondary" onclick="closeModal()">Закрыть</button>
                </div>
            </div>
        </div>
    `;

    document.getElementById('modals-container').innerHTML = modalHtml;
    document.querySelector('#modals-container .modal').style.display = 'flex';
}
async function showManageSubscriptionModal(data) {
    // Загружаем тарифные планы (если есть)
    let tariffPlans = [];
    try {
        const response = await api.get('/api/tariff-plans');
        if (response.success) {
            tariffPlans = response.plans;
        }
    } catch (error) {
        console.log('No tariff plans available');
    }

    const hasActiveSub = data.user.subscription && data.user.subscription.is_active;

    let tariffOptions = '';
    if (tariffPlans.length > 0) {
        tariffPlans.forEach(plan => {
            tariffOptions += `<option value="${plan.id}">${plan.name} - ${plan.price} ₽ (${plan.duration_days} дней)</option>`;
        });
    } else {
        tariffOptions = `
            <option value="">Нет тарифных планов</option>
            <option value="monthly">Месячная подписка</option>
            <option value="quarterly">Квартальная подписка</option>
            <option value="yearly">Годовая подписка</option>
        `;
    }

    const modalHtml = `
        <div class="modal">
            <div class="modal-content">
                <div class="modal-header">
                    <h2>Управление подпиской</h2>
                    <button class="close-btn" onclick="closeModal()">&times;</button>
                </div>
                <div class="modal-body">
                    <div style="margin-bottom: 20px;">
                        <h3>${data.user.full_name || 'Без имени'}</h3>
                        <p>@${data.user.username || 'нет'} | ID: ${data.user.telegram_id}</p>
                    </div>
                    
                    ${hasActiveSub ? `
                    <div style="background: rgba(16,185,129,0.1); padding: 15px; border-radius: 8px; margin-bottom: 20px;">
                        <h4>Текущая подписка</h4>
                        <p><strong>Тариф:</strong> ${data.user.subscription.tariff_name}</p>
                        <p><strong>Действует до:</strong> ${formatDate(data.user.subscription.end_date)}</p>
                        <p><strong>Лимит запросов:</strong> ${data.user.subscription.used_requests || 0}/${data.user.subscription.request_limit || 0}</p>
                        <div style="margin-top: 10px;">
                            <button class="btn btn-success" onclick="extendSubscription(${data.user.subscription.id})">
                                <i class="fas fa-plus"></i> Продлить
                            </button>
                            <button class="btn btn-danger" onclick="cancelSubscription(${data.user.subscription.id})">
                                <i class="fas fa-times"></i> Отменить
                            </button>
                        </div>
                    </div>
                    ` : `
                    <div style="background: rgba(100,116,139,0.1); padding: 15px; border-radius: 8px; margin-bottom: 20px;">
                        <h4>Нет активной подписки</h4>
                    </div>
                    `}
                    
                    <div style="margin-top: 20px;">
                        <h4>Добавить подписку</h4>
                        <form id="addSubscriptionForm">
                            ${tariffPlans.length > 0 ? `
                            <div style="margin-bottom: 15px;">
                                <label style="display: block; margin-bottom: 5px;">Тарифный план</label>
                                <select id="tariff-plan" class="filter-select" style="width: 100%;">
                                    ${tariffOptions}
                                </select>
                            </div>
                            ` : ''}
                            
                            <div style="margin-bottom: 15px;">
                                <label style="display: block; margin-bottom: 5px;">Название подписки</label>
                                <input type="text" id="plan-name" class="search-input" value="Месячная подписка" style="width: 100%;">
                            </div>
                            
                            <div style="margin-bottom: 15px;">
                                <label style="display: block; margin-bottom: 5px;">Длительность (дней)</label>
                                <input type="number" id="subscription-days" class="search-input" value="30" min="1" max="365" style="width: 100%;">
                            </div>
                        </form>
                    </div>
                </div>
                <div class="modal-footer">
                    <button class="btn btn-primary" onclick="addSubscription(${data.user.id})">
                        <i class="fas fa-plus"></i> Добавить подписку
                    </button>
                    <button class="btn btn-secondary" onclick="closeModal()">Отмена</button>
                </div>
            </div>
        </div>
    `;

    document.getElementById('modals-container').innerHTML = modalHtml;
    document.querySelector('#modals-container .modal').style.display = 'flex';
}

async function addSubscription(userId) {
    const tariffPlanId = document.getElementById('tariff-plan')?.value;
    const planName = document.getElementById('plan-name')?.value || 'Месячная подписка';
    const days = document.getElementById('subscription-days').value;

    if (!days || isNaN(days) || parseInt(days) <= 0) {
        api.showNotification('Введите корректное количество дней', 'error');
        return;
    }

    try {
        const data = {
            days: parseInt(days),
            plan_name: planName
        };

        if (tariffPlanId) {
            data.tariff_plan_id = parseInt(tariffPlanId);
        }

        const response = await api.post(`/api/user/${userId}/add_subscription`, data);

        if (response.success) {
            api.showNotification(response.message, 'success');
            closeModal();
            loadUsers(currentPage);
        }
    } catch (error) {
        console.error('Error adding subscription:', error);
    }
}
async function loadTariffPlans() {
    try {
        const response = await api.get('/api/tariff-plans');
        if (response.success) {
            return response.plans;
        }
        return [];
    } catch (error) {
        console.error('Error loading tariff plans:', error);
        return [];
    }
}



function closeModal() {
    document.getElementById('modals-container').innerHTML = '';
}

// Поиск с дебаунсом
let searchTimeout;
document.getElementById('user-search')?.addEventListener('input', (e) => {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => {
        loadUsers(1);
    }, 500);
});


// Добавьте эти глобальные функции в конец файла:

// Обновленная функция extendSubscription
async function extendSubscription(subId) {
    const days = prompt('На сколько дней продлить подписку?', '30');
    if (!days || isNaN(days) || parseInt(days) <= 0) {
        api.showNotification('Введите корректное количество дней', 'error');
        return;
    }

    try {
        const response = await api.post(`/api/subscription/${subId}/extend`, { days: parseInt(days) });
        if (response.success) {
            api.showNotification(response.message, 'success');
            closeModal();
            loadUsers(currentPage);
        }
    } catch (error) {
        console.error('Error extending subscription:', error);
    }
}

// Обновленная функция cancelSubscription
async function cancelSubscription(subId) {
    if (confirm('Отменить подписку?')) {
        try {
            const response = await api.post(`/api/subscription/${subId}/cancel`);
            if (response.success) {
                api.showNotification(response.message, 'success');
                closeModal();
                loadUsers(currentPage);
            }
        } catch (error) {
            console.error('Error canceling subscription:', error);
        }
    }
}

// Обновленная функция addSubscription
async function addSubscription(userId) {
    const days = document.getElementById('subscription-days').value;

    if (!days || isNaN(days) || parseInt(days) <= 0) {
        api.showNotification('Введите корректное количество дней', 'error');
        return;
    }

    try {
        const response = await api.post(`/api/user/${userId}/add_subscription`, {
            days: parseInt(days)
        });

        if (response.success) {
            api.showNotification(response.message, 'success');
            closeModal();
            loadUsers(currentPage);
        }
    } catch (error) {
        console.error('Error adding subscription:', error);
    }
}

// Обновленная функция showManageSubscriptionModal
async function showManageSubscriptionModal(data) {
    const hasActiveSub = data.user.subscription && data.user.subscription.is_active;

    const modalHtml = `
        <div class="modal">
            <div class="modal-content">
                <div class="modal-header">
                    <h2>Управление подпиской</h2>
                    <button class="close-btn" onclick="closeModal()">&times;</button>
                </div>
                <div class="modal-body">
                    <div style="margin-bottom: 20px;">
                        <h3>${data.user.full_name || 'Без имени'}</h3>
                        <p>@${data.user.username || 'нет'} | ID: ${data.user.telegram_id}</p>
                    </div>
                    
                    ${hasActiveSub ? `
                    <div style="background: rgba(16,185,129,0.1); padding: 15px; border-radius: 8px; margin-bottom: 20px;">
                        <h4>Текущая подписка</h4>
                        <p><strong>Действует до:</strong> ${formatDate(data.user.subscription.end_date)}</p>
                        <p><strong>Лимит запросов:</strong> ${data.user.subscription.used_requests || 0}/${data.user.subscription.request_limit || 0}</p>
                        <div style="margin-top: 10px;">
                            <button class="btn btn-success" onclick="extendSubscription(${data.user.subscription.id})">
                                <i class="fas fa-plus"></i> Продлить
                            </button>
                            <button class="btn btn-danger" onclick="cancelSubscription(${data.user.subscription.id})">
                                <i class="fas fa-times"></i> Отменить
                            </button>
                        </div>
                    </div>
                    ` : `
                    <div style="background: rgba(100,116,139,0.1); padding: 15px; border-radius: 8px; margin-bottom: 20px;">
                        <h4>Нет активной подписки</h4>
                    </div>
                    `}
                    
                    <div style="margin-top: 20px;">
                        <h4>Добавить подписку</h4>
                        <form id="addSubscriptionForm">
                            <div style="margin-bottom: 15px;">
                                <label style="display: block; margin-bottom: 5px;">Длительность (дней)</label>
                                <input type="number" id="subscription-days" class="search-input" value="30" min="1" max="365" style="width: 100%;">
                            </div>
                        </form>
                    </div>
                </div>
                <div class="modal-footer">
                    <button class="btn btn-primary" onclick="addSubscription(${data.user.id})">
                        <i class="fas fa-plus"></i> Добавить подписку
                    </button>
                    <button class="btn btn-secondary" onclick="closeModal()">Отмена</button>
                </div>
            </div>
        </div>
    `;

    document.getElementById('modals-container').innerHTML = modalHtml;
    document.querySelector('#modals-container .modal').style.display = 'flex';
}


window.showManageSubscriptionModal = showManageSubscriptionModal;

// Экспорт функций
window.loadUsers = loadUsers;
window.viewUserDetails = viewUserDetails;
window.manageUserSubscription = manageUserSubscription;
window.closeModal = closeModal;
window.extendSubscription = extendSubscription;
window.cancelSubscription = cancelSubscription;
window.addSubscription = addSubscription;