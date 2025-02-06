document.addEventListener("DOMContentLoaded", function () {
    // Удаление пользователя из проекта
    window.removeUserFromProject = async function (projectId, username) {
        if (!confirm(`Вы уверены, что хотите удалить пользователя ${username} из проекта?`)) return;

        try {
            const response = await fetch('/remove_user_from_project', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ project_id: projectId, username: username })
            });

            if (!response.ok) {
                const text = await response.text();
                throw new Error(`Ошибка: ${text}`);
            }

            const data = await response.json();
            alert(data.error || data.success);
            if (!data.error) location.reload();
        } catch (error) {
            console.error("Ошибка удаления пользователя:", error);
            alert("Ошибка при удалении пользователя.");
        }
    };

    // Валидация формы приглашения в проект
    window.validateInviteForm = function () {
        const userSelect = document.getElementById('user_id');
        if (!userSelect?.value) {
            alert("Пожалуйста, выберите пользователя для приглашения.");
            return false;
        }
        return true;
    };

    // Удаление проекта
    document.querySelectorAll('.delete-project').forEach(button => {
        button.addEventListener('click', async function () {
            const projectId = this.dataset.projectId;
            if (!confirm("Вы уверены, что хотите удалить этот проект?")) return;

            try {
                const response = await fetch("/delete_project", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ project_id: projectId })
                });

                const text = await response.text();
                let data;

                try {
                    data = JSON.parse(text);
                } catch (jsonError) {
                    console.error("Ошибка парсинга JSON:", jsonError, text);
                    alert("Ошибка удаления: Сервер вернул неожиданный ответ.");
                    return;
                }

                if (data.error) {
                    alert(data.error);
                } else {
                    alert("Проект удалён.");
                    location.reload();
                }
            } catch (error) {
                console.error("Ошибка удаления проекта:", error);
                alert("Ошибка удаления. Проверьте консоль.");
            }
        });
    });
});

document.querySelectorAll('.change-status').forEach(select => {
    select.addEventListener('change', async function() {
        const projectId = this.dataset.projectId;
        const newStatus = this.value;

        try {
            const response = await fetch(`/update_project_status/${projectId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ status: newStatus })
            });

            if (!response.ok) {
                throw new Error("Ошибка при обновлении статуса проекта.");
            }

            // Находим ячейку статуса проекта и обновляем текст
            document.querySelector(`#project-${projectId} .status-cell`).innerText = newStatus;
        } catch (error) {
            console.error("Ошибка при обновлении статуса проекта:", error);
        }
    });
});