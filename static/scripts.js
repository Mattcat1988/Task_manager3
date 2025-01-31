// Позволяет колонке принимать элемент
function allowDrop(event) {
    event.preventDefault();
}

// Инициализация перетаскивания
function drag(event) {
    event.dataTransfer.setData("text", event.target.id);
}

// Обработка перемещения и обновление на сервере
function drop(event, status, newProjectId) {
    event.preventDefault();
    let taskId = event.dataTransfer.getData("text");
    const taskElement = document.getElementById(taskId);

    // Извлечение только числового ID из taskId
    taskId = taskId.replace("task-", "");

    // Отправка запроса на сервер для обновления статуса задачи и ID проекта
    fetch(`/update_task_status/${taskId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ status: status, project_id: newProjectId })
    }).then(response => {
        if (response.ok) {
            const targetColumn = event.target.closest('.status-column');
            if (targetColumn) {
                targetColumn.appendChild(taskElement);
            } else {
                console.error('Не удалось найти целевую колонку');
            }
        } else {
            console.error('Ошибка сервера при обновлении статуса');
        }
    }).catch(error => {
        console.error('Ошибка при обновлении задачи:', error);
    });
}

// Удаление проекта

function deleteProject(projectId) {
    fetch(`/delete_project`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ project_id: projectId })
    }).then(response => {
        if (response.ok) {
            const projectElement = document.querySelector(`#project-${projectId}`);
            if (projectElement) {
                projectElement.remove();
            } else {
                console.error('Не удалось найти элемент проекта');
            }
        } else {
            console.error('Ошибка при удалении проекта');
        }
    }).catch(error => {
        console.error('Ошибка при удалении проекта:', error);
    });
}


// Удаление задачи
function deleteTask(taskId) {
    fetch(`/delete_task`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ task_id: taskId })
    }).then(response => {
        if (response.ok) {
            const taskElement = document.querySelector(`#task-${taskId}`);
            if (taskElement) {
                taskElement.remove();
            } else {
                console.error('Не удалось найти элемент задачи');
            }
        } else {
            console.error('Ошибка при удалении задачи');
        }
    }).catch(error => {
        console.error('Ошибка при удалении задачи:', error);
    });
}

// Переменные для хранения данных модального окна
let currentTaskId = null;

function openModal(taskId, description) {
    currentTaskId = taskId;
    // Декодируем строку обратно в текст
    const decodedDescription = decodeURIComponent(description);
    document.getElementById('taskDescription').value = decodedDescription || "";
    document.getElementById('descriptionModal').style.display = 'block';
}

function closeModal() {
    document.getElementById('descriptionModal').style.display = 'none';
}

function saveDescription() {
    const description = document.getElementById('taskDescription').value;

    fetch(`/update_task_description/${currentTaskId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ description: description })
    }).then(response => {
        if (response.ok) {
            closeModal();
            parent.location.reload();
        } else {
            console.error('Ошибка при сохранении описания');
        }
    }).catch(error => {
        console.error('Ошибка:', error);
    });
}
// Функция для фильтрации
function filterContacts() {
    let input = document.getElementById("search").value.toLowerCase();
    let contacts = document.getElementById("global-contacts").getElementsByTagName("li");
    for (let i = 0; i < contacts.length; i++) {
        let text = contacts[i].textContent.toLowerCase();
        contacts[i].style.display = text.includes(input) ? "" : "none";
    }
}
// Добавление и удаление контактов
function removeContact(contactId) {
    if (!confirm("Вы уверены, что хотите удалить этот контакт?")) {
        return;
    }

    fetch('/remove_contact', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ contact_id: contactId })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert("Контакт удалён.");
            location.reload();
        } else {
            alert("Ошибка при удалении контакта.");
        }
    })
    .catch(error => {
        console.error('Ошибка:', error);
    });
}
// Проверка контакта
function validateAddContactForm() {
    const contactSelect = document.getElementById('contact_id');
    if (!contactSelect.value) {
        alert("Выберите контакт перед добавлением.");
        return false;
    }
    return true;
}
// Проверка передачи ID
function validateTaskForm() {
    const title = document.querySelector("input[name='title']").value.trim();
    const assignee = document.querySelector("select[name='assignee_id']").value;

    if (!title) {
        alert("Введите название задачи.");
        return false;
    }
    if (!assignee) {
        alert("Выберите пользователя, на которого назначена задача.");
        return false;
    }
    return true;
}
// Функции для редактирования названия задачи
function showEditTaskTitle(taskId) {
    document.getElementById(`task-title-${taskId}`).style.display = 'none';
    document.getElementById(`edit-task-title-${taskId}`).style.display = 'block';
}

function cancelEditTaskTitle(taskId) {
    document.getElementById(`task-title-${taskId}`).style.display = 'block';
    document.getElementById(`edit-task-title-${taskId}`).style.display = 'none';
}

function saveTaskTitle(taskId) {
    const newTitle = document.getElementById(`new-title-${taskId}`).value;

    fetch(`/update_task_title/${taskId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ title: newTitle })
    }).then(response => {
        if (response.ok) {
            document.getElementById(`task-title-${taskId}`).innerText = newTitle;
            cancelEditTaskTitle(taskId);
        } else {
            console.error('Ошибка при обновлении названия задачи');
        }
    }).catch(error => {
        console.error('Ошибка:', error);
    });
}

// Функции для открытия и закрытия модального окна редактирования названия задачи
//let currentTaskId = null;

function openTitleModal(taskId, title) {
    currentTaskId = taskId;  // Записываем ID задачи
    document.getElementById('taskTitleInput').value = title; // Устанавливаем текущее название задачи в поле ввода
    document.getElementById('titleModal').style.display = 'block'; // Показываем модальное окно
}

function closeTitleModal() {
    document.getElementById('titleModal').style.display = 'none'; // Скрываем модальное окно
}

function saveTitle() {
    const newTitle = document.getElementById('taskTitleInput').value;

    fetch(`/update_task_title/${currentTaskId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ title: newTitle })
    }).then(response => {
        if (response.ok) {
            document.getElementById(`task-title-${currentTaskId}`).innerText = newTitle;
            closeTitleModal();
        } else {
            console.error('Ошибка при обновлении названия задачи');
        }
    }).catch(error => {
        console.error('Ошибка:', error);
    });
}
function showTooltip(event, description) {
    const tooltip = event.target.querySelector('.tooltip-text');
    tooltip.innerText = description || "Нет описания";
    tooltip.style.visibility = 'visible';
}

function hideTooltip(event) {
    const tooltip = event.target.querySelector('.tooltip-text');
    tooltip.style.visibility = 'hidden';
}

//Удаление пользователя из проекта
function removeUserFromProject(projectId, username) {
    if (!confirm(`Вы уверены, что хотите удалить пользователя ${username} из проекта?`)) {
        return;
    }

    fetch('/remove_user_from_project', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ project_id: projectId, username: username })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            // Отображаем соответствующее сообщение об ошибке, если удаление невозможно
            alert(data.error);
        } else {
            // Сообщение об успешном удалении
            alert(data.success);
            location.reload();  // Перезагрузка страницы для обновления списка участников
        }
    })
    .catch(error => {
        console.error('Ошибка:', error);
        alert('Произошла ошибка при удалении пользователя.');
    });
}
function validateInviteForm() {
    const userSelect = document.getElementById('user_id');
    if (userSelect.value === "") {
        alert("Пожалуйста, выберите пользователя для приглашения.");
        return false;  // Предотвращаем отправку формы
    }
    return true;
}
// Удаление контакта
function deleteContact(contactId) {
    if (!confirm("Вы уверены, что хотите удалить этот контакт?")) return;

    fetch(`/delete_contact/${contactId}`, { method: 'POST' })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            location.reload();
        } else {
            alert("Ошибка при удалении контакта.");
        }
    })
    .catch(error => console.error('Ошибка:', error));
}

// Открытие модального окна редактирования
function editContact(id, firstName, lastName, email, phone) {
    document.getElementById("editContactId").value = id;
    document.getElementById("editFirstName").value = firstName || "";
    document.getElementById("editLastName").value = lastName || "";
    document.getElementById("editEmail").value = email || "";
    document.getElementById("editPhone").value = phone || "";

    document.getElementById("editContactModal").style.display = "block";
}

// Закрытие модального окна
function closeEditModal() {
    document.getElementById("editContactModal").style.display = "none";
}

// Сохранение отредактированного контакта
function saveContact() {
    const id = document.getElementById("editContactId").value;
    const firstName = document.getElementById("editFirstName").value;
    const lastName = document.getElementById("editLastName").value;
    const email = document.getElementById("editEmail").value;
    const phone = document.getElementById("editPhone").value;

    fetch('/edit_contact', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id, first_name: firstName, last_name: lastName, email, phone })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            closeEditModal();
            location.reload();
        } else {
            alert("Ошибка при сохранении контакта.");
        }
    })
    .catch(error => console.error('Ошибка:', error));
}