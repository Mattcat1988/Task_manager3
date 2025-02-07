document.addEventListener("DOMContentLoaded", function () {
    // Фильтрация контактов
    window.filterContacts = function () {
        const input = document.getElementById("search")?.value.toLowerCase();
        const contacts = document.querySelectorAll("#global-contacts li");

        if (!input || contacts.length === 0) return;

        contacts.forEach(contact => {
            contact.style.display = contact.textContent.toLowerCase().includes(input) ? "" : "none";
        });
    };
            function filterContacts() {
            let input = document.getElementById("search").value.toLowerCase();
            let contacts = document.getElementById("global-contacts").getElementsByTagName("li");
            for (let i = 0; i < contacts.length; i++) {
                let text = contacts[i].textContent.toLowerCase();
                contacts[i].style.display = text.includes(input) ? "" : "none";
            }
        }

function openContactModal(id, firstName, lastName, email, phone, notes) {
    document.getElementById("modalContactName").innerText = `${firstName} ${lastName}`;
    document.getElementById("modalEmail").innerText = email && email !== "None" ? email : "Нет данных";
    document.getElementById("modalPhone").innerText = phone && phone !== "None" ? phone : "Нет данных";
    document.getElementById("modalNotes").innerText = notes && notes !== "None" ? notes : "Нет заметок";
    document.getElementById("contactModal").style.display = "block";
}

        function closeContactModal() {
            document.getElementById("contactModal").style.display = "none";
        }

        function deleteContact(contactId) {
            if (!confirm("Вы уверены, что хотите удалить этот контакт?")) {
                return;
            }

            fetch('/delete_contact', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ contact_id: contactId })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert(data.success);
                    location.reload();
                } else if (data.error) {
                    alert(data.error);
                }
            })
            .catch(error => {
                console.error('Ошибка при удалении контакта:', error);
                alert('Произошла ошибка при удалении контакта.');
            });
        }

    // Удаление контакта
    window.deleteContact = function (contactId) {
        if (!confirm("Вы уверены, что хотите удалить этот контакт?")) return;

        fetch(`/delete_contact/${contactId}`, { method: 'POST' })
            .then(response => {
                if (!response.ok) {
                    return response.text().then(text => { throw new Error(text); });
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    alert("Контакт удалён.");
                    location.reload();
                } else {
                    alert("Ошибка при удалении контакта.");
                }
            })
            .catch(error => {
                console.error("Ошибка при удалении контакта:", error);
                alert("Ошибка при удалении контакта: " + error.message);
            });
    };

    // Открытие модального окна редактирования контакта
    window.editContact = function (id, firstName, lastName, email, phone) {
        document.getElementById("editContactId")?.setAttribute("value", id);
        document.getElementById("editFirstName")?.setAttribute("value", firstName || "");
        document.getElementById("editLastName")?.setAttribute("value", lastName || "");
        document.getElementById("editEmail")?.setAttribute("value", email || "");
        document.getElementById("editPhone")?.setAttribute("value", phone || "");

        const modal = document.getElementById("editContactModal");
        if (modal) modal.style.display = "block";
    };

    // Закрытие модального окна
    window.closeEditModal = function () {
        const modal = document.getElementById("editContactModal");
        if (modal) modal.style.display = "none";
    };

    // Сохранение изменений контакта
    window.saveContact = function () {
        const id = document.getElementById("editContactId")?.value;
        const firstName = document.getElementById("editFirstName")?.value;
        const lastName = document.getElementById("editLastName")?.value;
        const email = document.getElementById("editEmail")?.value;
        const phone = document.getElementById("editPhone")?.value;

        if (!id) {
            alert("Ошибка: ID контакта отсутствует.");
            return;
        }

        fetch('/edit_contact', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ id, first_name: firstName, last_name: lastName, email, phone })
        })
            .then(response => {
                if (!response.ok) {
                    return response.text().then(text => { throw new Error(text); });
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    closeEditModal();
                    location.reload();
                } else {
                    alert("Ошибка при сохранении контакта.");
                }
            })
            .catch(error => {
                console.error("Ошибка при сохранении контакта:", error);
                alert("Ошибка при сохранении контакта: " + error.message);
            });
    };

    // Проверка перед добавлением контакта
    window.validateAddContactForm = function () {
        const contactSelect = document.getElementById("contact_id");
        if (!contactSelect?.value) {
            alert("Выберите контакт перед добавлением.");
            return false;
        }
        return true;
    };
});