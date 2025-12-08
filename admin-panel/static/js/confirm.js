// Управление модальными окнами подтверждения

let currentConfirmCallback = null;

function showConfirmModal(title, message, callback) {
    const template = document.getElementById('confirm-modal-template');
    const modalHtml = template.innerHTML;

    document.getElementById('modal-container').innerHTML = modalHtml;

    const modal = document.querySelector('#modal-container .modal');
    modal.style.display = 'flex';

    document.getElementById('confirm-modal-title').textContent = title;
    document.getElementById('confirm-modal-message').textContent = message;

    currentConfirmCallback = callback;

    document.getElementById('confirm-modal-yes').onclick = () => {
        if (currentConfirmCallback) {
            currentConfirmCallback();
        }
        closeConfirmModal();
    };
}

function closeConfirmModal() {
    const modal = document.querySelector('#modal-container .modal');
    if (modal) {
        modal.style.display = 'none';
        document.getElementById('modal-container').innerHTML = '';
    }
    currentConfirmCallback = null;
}

// Глобальные функции для использования в HTML
window.showConfirmModal = showConfirmModal;
window.closeConfirmModal = closeConfirmModal;