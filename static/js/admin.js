document.addEventListener("DOMContentLoaded", function () {
    const createUserModal = document.getElementById('createUserModal');
    const createUserBtn = document.getElementById('createUserBtn');
    const changePasswordModal = document.getElementById('changePasswordModal');
    const createUserForm = document.getElementById('createUserForm');
    const changePasswordForm = document.getElementById('changePasswordForm');
    const ldapSettingsForm = document.getElementById('ldapSettingsForm');
    let currentUserId = null;

    // Открытие модального окна создания пользователя
    if (createUserBtn && createUserModal) {
        createUserBtn.addEventListener("click", function () {
            createUserModal.style.display = 'block';
        });
    }

    // Закрытие модального окна создания пользователя
    window.closeCreateUserModal = function () {
        if (createUserModal) {
            createUserModal.style.display = 'none';
        }
    };

    // Открытие модального окна смены пароля
    window.openChangePasswordModal = function (userId) {
        currentUserId = userId;
        if (changePasswordModal) {
            changePasswordModal.style.display = 'block';
        }
    };

    // Закрытие модального окна смены пароля
    window.closeChangePasswordModal = function () {
        if (changePasswordModal) {
            changePasswordModal.style.display = 'none';
        }
    };

    // Закрытие модальных окон при клике вне их
    window.onclick = function (event) {
        if (event.target === createUserModal) {
            closeCreateUserModal();
        }
        if (event.target === changePasswordModal) {
            closeChangePasswordModal();
        }
    };

    // Обработчик формы создания пользователя
    if (createUserForm) {
        createUserForm.onsubmit = function (event) {
            event.preventDefault();
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            const isAdmin = document.getElementById('is_admin').checked;

            fetch('/admin/create_user_async', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    username: username,
                    password: password,
                    is_admin: isAdmin
                })
            })
                .then(response => {
                    if (!response.ok) {
                        return response.text().then(text => { throw new Error(text) });
                    }
                    return response.json();
                })
                .then(data => {
                    if (data.error) {
                        alert(data.error);
                    } else {
                        alert(data.success);
                        closeCreateUserModal();
                        window.location.reload();
                    }
                })
                .catch(error => {
                    console.error('Ошибка при создании пользователя:', error);
                    alert("Ошибка при создании пользователя: " + error.message);
                });
        };
    }

    // Обработчик формы смены пароля
    if (changePasswordForm) {
        changePasswordForm.onsubmit = function (event) {
            event.preventDefault();
            const newPassword = document.getElementById('newPassword').value;

            fetch(`/admin/change_password_async/${currentUserId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ password: newPassword })
            })
                .then(response => {
                    if (!response.ok) {
                        return response.text().then(text => { throw new Error(text) });
                    }
                    return response.json();
                })
                .then(data => {
                    if (data.error) {
                        alert(data.error);
                    } else {
                        alert(data.success);
                        closeChangePasswordModal();
                    }
                })
                .catch(error => {
                    console.error('Ошибка при смене пароля:', error);
                    alert("Ошибка при смене пароля: " + error.message);
                });
        };
    }

    // Функция удаления пользователя
    window.deleteUser = function (userId) {
        if (!confirm("Вы уверены, что хотите удалить пользователя?")) return;

        fetch(`/admin/delete_user/${userId}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
        })
            .then(response => {
                if (!response.ok) {
                    return response.text().then(text => { throw new Error(text) });
                }
                return response.json();
            })
            .then(data => {
                if (data.error) {
                    alert(data.error);
                } else {
                    alert(data.success);
                    window.location.reload();
                }
            })
            .catch(error => {
                console.error('Ошибка удаления:', error);
                alert("Ошибка удаления пользователя: " + error.message);
            });
    };

    // Сохранение настроек LDAP
    if (ldapSettingsForm) {
        window.saveLdapSettings = function () {
            const formData = new FormData(ldapSettingsForm);
            const jsonData = {};
            formData.forEach((value, key) => {
                jsonData[key] = value;
            });

            fetch("/admin/save_ldap_settings", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(jsonData)
            })
                .then(response => {
                    if (!response.ok) {
                        return response.text().then(text => { throw new Error(text) });
                    }
                    return response.json();
                })
                .then(data => alert(data.message))
                .catch(error => {
                    console.error('Ошибка сохранения LDAP:', error);
                    alert("Ошибка сохранения: " + error.message);
                });
        };
    }

    // Проверка соединения с LDAP
    window.testLdapConnection = function () {
        fetch("/admin/test_ldap_connection", { method: "POST" })
            .then(response => {
                if (!response.ok) {
                    return response.text().then(text => { throw new Error(text) });
                }
                return response.json();
            })
            .then(data => alert(data.message))
            .catch(error => {
                console.error('Ошибка тестирования LDAP:', error);
                alert("Ошибка тестирования: " + error.message);
            });
    };
});