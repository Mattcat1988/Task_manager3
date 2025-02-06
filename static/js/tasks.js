document.addEventListener("DOMContentLoaded", function () {
    let currentTaskId = null;

    // Редактирование названия задачи
    window.showEditTaskTitle = function (taskId) {
        document.getElementById(`task-title-${taskId}`)?.classList.add('hidden');
        document.getElementById(`edit-task-title-${taskId}`)?.classList.remove('hidden');
    };

    window.cancelEditTaskTitle = function (taskId) {
        document.getElementById(`task-title-${taskId}`)?.classList.remove('hidden');
        document.getElementById(`edit-task-title-${taskId}`)?.classList.add('hidden');
    };

    window.saveTaskTitle = async function (taskId) {
        const newTitle = document.getElementById(`new-title-${taskId}`)?.value;

        if (!newTitle) {
            alert("Введите новое название задачи.");
            return;
        }

try {
    const response = await fetch(`/update_task_title/${taskId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: newTitle })
    });

    const data = await response.json(); // Читаем JSON-ответ

    if (!response.ok) {
        throw new Error(data.error || "Ошибка при обновлении названия задачи.");
    }

    document.getElementById(`task-title-${taskId}`).innerText = newTitle;
    window.cancelEditTaskTitle(taskId);
} catch (error) {
    console.error("Ошибка при сохранении названия задачи:", error);
    alert("Ошибка: " + error.message); // Вывести сообщение пользователю
}

    // Открытие и закрытие модального окна редактирования задачи
    window.openTitleModal = function (taskId, title) {
        currentTaskId = taskId;
        document.getElementById('taskTitleInput').value = title || "";
        document.getElementById('titleModal')?.classList.add('visible');
    };

    window.closeTitleModal = function () {
        document.getElementById('titleModal')?.classList.remove('visible');
    };

    window.saveTitle = async function () {
        const newTitle = document.getElementById('taskTitleInput')?.value;

        if (!newTitle) {
            alert("Введите название задачи.");
            return;
        }

        try {
            const response = await fetch(`/update_task_title/${currentTaskId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ title: newTitle })
            });

            if (!response.ok) {
                throw new Error("Ошибка при обновлении названия задачи.");
            }

            document.getElementById(`task-title-${currentTaskId}`).innerText = newTitle;
            window.closeTitleModal();
        } catch (error) {
            console.error("Ошибка:", error);
        }
    };

    // Удаление задачи
    window.deleteTask = async function (taskId) {
        if (!confirm("Вы уверены, что хотите удалить эту задачу?")) return;

        try {
            const response = await fetch(`/delete_task`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ task_id: taskId })
            });

            if (!response.ok) {
                throw new Error("Ошибка при удалении задачи.");
            }

            document.querySelector(`#task-${taskId}`)?.remove();
        } catch (error) {
            console.error("Ошибка при удалении задачи:", error);
            alert("Ошибка при удалении задачи.");
        }
    };

    // Перемещение задачи между колонками
    window.drop = async function (event, status, newProjectId) {
        event.preventDefault();
        let taskId = event.dataTransfer.getData("text");
        const taskElement = document.getElementById(taskId);

        taskId = taskId.replace("task-", "");

        try {
            const response = await fetch(`/update_task_status/${taskId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ status: status, project_id: newProjectId })
            });

            if (!response.ok) {
                throw new Error("Ошибка сервера при обновлении статуса.");
            }

            const targetColumn = event.target.closest('.status-column');
            if (targetColumn) {
                targetColumn.appendChild(taskElement);
            } else {
                console.error("Не удалось найти целевую колонку.");
            }
        } catch (error) {
            console.error("Ошибка при обновлении задачи:", error);
        }
    };

    // Открытие и закрытие модального окна описания задачи
    window.openModal = function (taskId, description) {
        currentTaskId = taskId;
        document.getElementById('taskDescription').value = decodeURIComponent(description) || "";
        document.getElementById('descriptionModal')?.classList.add('visible');
    };

    window.closeModal = function () {
        document.getElementById('descriptionModal')?.classList.remove('visible');
    };

    window.saveDescription = async function () {
        const description = document.getElementById('taskDescription')?.value;

        try {
            const response = await fetch(`/update_task_description/${currentTaskId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ description: description })
            });

            if (!response.ok) {
                throw new Error("Ошибка при сохранении описания.");
            }

            window.closeModal();
            location.reload();
        } catch (error) {
            console.error("Ошибка:", error);
        }
    };

    // Валидация формы задачи перед отправкой
    window.validateTaskForm = function () {
        const title = document.querySelector("input[name='title']")?.value.trim();
        const assignee = document.querySelector("select[name='assignee_id']")?.value;

        if (!title) {
            alert("Введите название задачи.");
            return false;
        }
        if (!assignee) {
            alert("Выберите пользователя, на которого назначена задача.");
            return false;
        }
        return true;
    };
});