// Функции для управления инструкциями

async function loadInstructions() {
    try {
        const response = await api.get('/instructions');

        if (response.success) {
            updateInstructionsTable(response.instructions);
        }

        // Настройка кнопок действий
        const actionsContainer = document.getElementById('instructions-header-actions');
        actionsContainer.innerHTML = `
            <button class="btn btn-primary" onclick="showAddInstructionModal()">
                <i class="fas fa-plus"></i> Добавить
            </button>
        `;

    } catch (error) {
        console.error('Error loading instructions:', error);
    }
}

function updateInstructionsTable(instructions) {
    const tbody = document.getElementById('instructions-table-body');
    tbody.innerHTML = '';

    instructions.forEach(inst => {
        const videoLink = inst.video_url
            ? `<a href="${inst.video_url}" target="_blank" class="text-accent">Ссылка</a>`
            : '<span class="text-muted">Нет</span>';

        const row = `<tr>
            <td><strong>${inst.order_index}</strong></td>
            <td><strong>${inst.title}</strong></td>
            <td>${inst.text_content.substring(0, 80)}${inst.text_content.length > 80 ? '...' : ''}</td>
            <td>${videoLink}</td>
            <td>
                <button class="btn btn-sm btn-primary" onclick="editInstruction(${inst.id})">
                    <i class="fas fa-edit"></i>
                </button>
                <button class="btn btn-sm btn-danger" onclick="deleteInstruction(${inst.id})">
                    <i class="fas fa-trash"></i>
                </button>
            </td>
        </tr>`;

        tbody.innerHTML += row;
    });
}

function showAddInstructionModal() {
    const modalHtml = `
        <div class="modal" id="addInstructionModal">
            <div class="modal-content">
                <div class="modal-header">
                    <h2>Добавить инструкцию</h2>
                    <button class="close-btn" onclick="closeModal('addInstructionModal')">&times;</button>
                </div>
                <div class="modal-body">
                    <form id="instructionForm">
                        <div class="form-group">
                            <label class="form-label">Заголовок</label>
                            <input type="text" id="instructionTitle" class="form-control" required>
                        </div>
                        <div class="form-group">
                            <label class="form-label">Текст инструкции</label>
                            <textarea id="instructionContent" class="form-control" rows="8" required></textarea>
                        </div>
                        <div class="form-group">
                            <label class="form-label">Ссылка на видео (опционально)</label>
                            <input type="url" id="instructionVideo" class="form-control" placeholder="https://...">
                        </div>
                        <div class="form-group">
                            <label class="form-label">Порядковый номер</label>
                            <input type="number" id="instructionOrder" class="form-control" value="1" min="1">
                        </div>
                    </form>
                </div>
                <div class="modal-footer">
                    <button class="btn btn-primary" onclick="saveInstruction()">Сохранить</button>
                    <button class="btn btn-secondary" onclick="closeModal('addInstructionModal')">Отмена</button>
                </div>
            </div>
        </div>
    `;

    document.body.insertAdjacentHTML('beforeend', modalHtml);
    document.getElementById('addInstructionModal').style.display = 'flex';
}

async function saveInstruction() {
    try {
        const title = document.getElementById('instructionTitle').value.trim();
        const content = document.getElementById('instructionContent').value.trim();
        const videoUrl = document.getElementById('instructionVideo').value.trim();
        const orderIndex = document.getElementById('instructionOrder').value;

        if (!title || !content) {
            api.showNotification('Заголовок и текст обязательны', 'error');
            return;
        }

        const response = await api.post('/instructions', {
            title: title,
            content: content,
            video_url: videoUrl || null,
            order_index: parseInt(orderIndex) || 1
        });

        if (response.success) {
            api.showNotification(response.message, 'success');
            closeModal('addInstructionModal');
            loadInstructions();
        }

    } catch (error) {
        console.error('Error saving instruction:', error);
    }
}

function editInstruction(instId) {
    showEditInstructionModal(instId);
}

async function deleteInstruction(instId) {
    if (confirm('Вы уверены, что хотите удалить инструкцию? Эту операцию нельзя отменить.')) {
        try {
            // Здесь можно добавить API для удаления инструкции
            api.showNotification('Функция удаления инструкции находится в разработке', 'warning');
            // loadInstructions();
        } catch (error) {
            console.error('Error deleting instruction:', error);
        }
    }
}

function reorderInstructions() {
    api.showNotification('Функция изменения порядка инструкций находится в разработке', 'warning');
}

async function showEditInstructionModal(instId) {
    try {
        // Здесь можно загрузить данные инструкции и показать модальное окно редактирования
        // const response = await api.get(`/instructions/${instId}`);
        // if (response.success) {
        //     // Показать модальное окно с данными
        // }

        api.showNotification('Функция редактирования инструкции находится в разработке', 'warning');

    } catch (error) {
        console.error('Error loading instruction for edit:', error);
    }
}