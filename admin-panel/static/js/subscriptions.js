async function loadSubscriptions() {
    try {
        const filter = document.getElementById('subscription-filter')?.value || 'all';

        const response = await api.get('/api/subscriptions', {
            status: filter !== 'all' ? filter : ''
        });

        if (response.success) {
            updateSubscriptionsTable(response.subscriptions);
        }
    } catch (error) {
        console.error('Error loading subscriptions:', error);
    }
}

function updateSubscriptionsTable(subscriptions) {
    const tbody = document.getElementById('subscriptions-table-body');
    tbody.innerHTML = '';

    if (subscriptions.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6" class="text-center">Нет подписок</td>
            </tr>
        `;
        return;
    }

    subscriptions.forEach(sub => {
        const endDate = new Date(sub.end_date);
        const daysLeft = Math.ceil((endDate - new Date()) / (1000 * 60 * 60 * 24));

        let statusBadge = '';
        let statusClass = '';

        if (sub.is_active && daysLeft > 0) {
            statusBadge = `<span class="badge badge-success">Активна (${daysLeft} дн.)</span>`;
            statusClass = daysLeft < 7 ? 'text-warning' : 'text-success';
        } else {
            statusBadge = '<span class="badge badge-danger">Истекла</span>';
            statusClass = 'text-danger';
        }

        const row = document.createElement('tr');
        row.innerHTML = `
            <td>
                <div><strong>${sub.user.full_name || 'Без имени'}</strong></div>
                <div style="font-size: 12px; color: #94a3b8;">@${sub.user.username || 'нет'}</div>
            </td>
            <td><span class="badge badge-info">${sub.tariff_name}</span></td>
            <td>${formatDate(sub.start_date)}</td>
            <td>
                ${formatDate(sub.end_date)}
                <div style="font-size: 12px;" class="${statusClass}">
                    ${sub.is_active && daysLeft > 0 ? `Осталось: ${daysLeft} дн.` : 'Истекла'}
                </div>
            </td>
            <td>${statusBadge}</td>
            <td>
                <button class="btn btn-sm btn-success" onclick="extendSubscription(${sub.id})">
                    <i class="fas fa-plus"></i>
                </button>
                <button class="btn btn-sm btn-danger" onclick="cancelSubscription(${sub.id})">
                    <i class="fas fa-times"></i>
                </button>
                <button class="btn btn-sm btn-secondary" onclick="viewUserDetails(${sub.user.id})">
                    <i class="fas fa-eye"></i>
                </button>
            </td>
        `;

        tbody.appendChild(row);
    });
}
// Обработчик изменения фильтра
document.getElementById('subscription-filter')?.addEventListener('change', (e) => {
    loadSubscriptions();
});

// Экспорт функций
window.loadSubscriptions = loadSubscriptions;