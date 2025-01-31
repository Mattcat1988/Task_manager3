from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash
import sqlite3
from ldap3 import Server, Connection, ALL, SIMPLE, SUBTREE
from ldap3.core.exceptions import LDAPBindError
import json
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Секретный ключ для сессий

# Подключение к базе данных
def get_db_connection():
    conn = sqlite3.connect('kanban.db', check_same_thread=False, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


# Функция получения настроек LDAP
def get_ldap_config():
    conn = get_db_connection()
    config = conn.execute("SELECT * FROM ldap_settings WHERE id = 1").fetchone()
    conn.close()

    if not config:
        print("⚠ Настройки LDAP отсутствуют в БД!")
        return None

    ldap_config = {
        "server": config["server"],
        "port": config["port"],
        "bind_user": config["bind_user"],
        "bind_password": config["bind_password"],
        "base_dn": config["base_dn"],
        "user_attr": config["user_attr"]
    }

    # Кэшируем настройки в JSON-файл
    with open("ldap_config.json", "w", encoding="utf-8") as f:
        json.dump(ldap_config, f, indent=4)

    return ldap_config
#Загрузка LDAP
def load_ldap_config():
    try:
        with open("ldap_config.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return None
def ldap_authenticate(username, password):
    try:
        ldap_settings = get_ldap_config()
        if not ldap_settings:
            print("Ошибка: Настройки LDAP не загружены.")
            return False

        server = Server(ldap_settings['server'], port=ldap_settings['port'], get_info=ALL)
        conn = Connection(
            server,
            user=ldap_settings['bind_user'],
            password=ldap_settings['bind_password'],
            auto_bind=True
        )
        search_filter = f"({ldap_settings['user_attr']}={username})"
        conn.search(ldap_settings['base_dn'], search_filter, search_scope=SUBTREE, attributes=['cn', 'givenName', 'sn'])

        if not conn.entries:
            return False

        user_dn = conn.entries[0].entry_dn
        user_conn = Connection(server, user=user_dn, password=password, authentication=SIMPLE)

        if user_conn.bind():
            first_name = conn.entries[0]['givenName'].value if 'givenName' in conn.entries[0] else None
            last_name = conn.entries[0]['sn'].value if 'sn' in conn.entries[0] else None
            middle_name = None
            if 'cn' in conn.entries[0]:
                full_name = conn.entries[0]['cn'].value
                full_name_parts = full_name.split()
                if len(full_name_parts) > 2:
                    middle_name = " ".join(full_name_parts[1:-1])
                first_name = first_name or full_name_parts[0]
                last_name = last_name or full_name_parts[-1]

            # Сохраняем данные в БД, если их нет
            conn_db = get_db_connection()
            user_in_db = conn_db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()

            if not user_in_db:
                conn_db.execute(
                    'INSERT INTO users (username, first_name, last_name, middle_name, is_admin) VALUES (?, ?, ?, ?, ?)',
                    (username, first_name, last_name, middle_name, 0)
                )
                conn_db.commit()
                user_in_db = conn_db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()

            # Сохранение информации о пользователе в сессии, включая числовой user_id
            session['is_ldap_user'] = True
            session['user_id'] = user_in_db['id']
            session['is_admin'] = 0
            session['first_name'] = first_name
            session['last_name'] = last_name
            session['middle_name'] = middle_name

            conn_db.close()
            return True
        else:
            return False
    except LDAPBindError:
        return False


# Инициализация базы данных с созданием администратора
def init_db():
    conn = get_db_connection()
    with open('schema.sql') as f:
        conn.executescript(f.read())

    # Проверяем, существует ли администратор
    admin_user = conn.execute('SELECT * FROM users WHERE username = ?', ('admin',)).fetchone()

    # Если администратора нет, создаем его с паролем "admin"
    if not admin_user:
        hashed_password = generate_password_hash('admin', method='pbkdf2:sha256', salt_length=16)
        conn.execute('INSERT INTO users (username, password, is_admin) VALUES (?, ?, ?)',
                     ('admin', hashed_password, True))
        conn.commit()

    conn.close()

# Проверка роли администратора
def is_admin():
    return session.get('is_admin', False)



# Админская панель для управления пользователями
@app.route('/admin')
def admin_panel():
    if 'is_admin' not in session or not session['is_admin']:
        return redirect(url_for('index'))

    conn = get_db_connection()
    users = conn.execute('SELECT id, username, is_admin FROM users').fetchall()

    # Получаем сохранённые настройки LDAP из базы (пример)
    ldap_config = conn.execute('SELECT * FROM ldap_settings LIMIT 1').fetchone()

    conn.close()

    return render_template('admin_panel.html', users=users, ldap_config=ldap_config)
#Сохранение настроек LDAP
@app.route('/admin/save_ldap_settings', methods=['POST'])
def save_ldap_settings():
    data = request.json  # Получаем JSON
    print("📥 Полученные данные:", data)  # Логируем

    # Проверяем, пришли ли корректные данные
    required_keys = ['ldap_server', 'ldap_port', 'ldap_bind_user', 'ldap_bind_password', 'ldap_base_dn', 'ldap_user_attr']
    if not all(key in data for key in required_keys):
        return jsonify({"error": "Некорректные данные. Отсутствуют обязательные поля"}), 400

    try:
        conn = get_db_connection()

        # Проверяем, есть ли уже настройки LDAP
        existing = conn.execute("SELECT id FROM ldap_settings WHERE id = 1").fetchone()

        if existing:
            print("🔄 Обновляем существующие настройки LDAP в БД")
            conn.execute("""
                UPDATE ldap_settings
                SET server = ?, port = ?, bind_user = ?, bind_password = ?, base_dn = ?, user_attr = ?
                WHERE id = 1
            """, (data['ldap_server'], data['ldap_port'], data['ldap_bind_user'],
                  data['ldap_bind_password'], data['ldap_base_dn'], data['ldap_user_attr']))
        else:
            print("🆕 Создаём запись с настройками LDAP")
            conn.execute("""
                INSERT INTO ldap_settings (id, server, port, bind_user, bind_password, base_dn, user_attr)
                VALUES (1, ?, ?, ?, ?, ?, ?)
            """, (data['ldap_server'], data['ldap_port'], data['ldap_bind_user'],
                  data['ldap_bind_password'], data['ldap_base_dn'], data['ldap_user_attr']))

        conn.commit()
        conn.close()

        # Сохраняем настройки в JSON-файл (кешируем)
        with open("ldap_config.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

        return jsonify({"message": "Настройки LDAP успешно сохранены"}), 200

    except Exception as e:
        return jsonify({"error": f"Ошибка сохранения LDAP: {str(e)}"}), 500
#Проверка ldap соединения
@app.route('/admin/test_ldap_connection', methods=['POST'])
def test_ldap_connection():
    ldap_settings = get_ldap_config()

    if not ldap_settings:
        return jsonify({"error": "Настройки LDAP не загружены"}), 400

    try:
        server = Server(ldap_settings['server'], port=int(ldap_settings['port']), get_info=ALL)
        conn = Connection(
            server,
            user=ldap_settings['bind_user'],
            password=ldap_settings['bind_password'],
            auto_bind=True
        )

        if conn.bind():
            return jsonify({"message": "Соединение с LDAP установлено успешно"}), 200
        else:
            return jsonify({"error": "Не удалось подключиться к серверу LDAP"}), 400

    except Exception as e:
        return jsonify({"error": f"Ошибка при подключении к LDAP: {str(e)}"}), 500

# Обработка AJAX-запроса для создания нового пользователя
@app.route('/admin/create_user_async', methods=['POST'])
def create_user_async():
    if not is_admin():
        return jsonify({'error': 'Доступ запрещен.'}), 403

    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    is_admin_flag = 1 if data.get('is_admin') else 0

    hashed_password = generate_password_hash(password, method='pbkdf2:sha256', salt_length=16)

    conn = get_db_connection()
    try:
        conn.execute("INSERT INTO users (username, password, is_admin) VALUES (?, ?, ?)",
                     (username, hashed_password, is_admin_flag))
        conn.commit()
        return jsonify({'success': 'Пользователь успешно создан.'}), 200
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Имя пользователя уже существует.'}), 400
    finally:
        conn.close()  # Обязательно закрываем соединение
#Смена роли
@app.route('/admin/change_user_role/<int:user_id>', methods=['POST'])
def change_user_role(user_id):
    if not is_admin():
        flash("Доступ запрещен. Только для администраторов.")
        return redirect(url_for('admin_panel'))

    new_role = int(request.form['is_admin'])

    conn = get_db_connection()
    conn.execute('UPDATE users SET is_admin = ? WHERE id = ?', (new_role, user_id))
    conn.commit()
    conn.close()

    flash("Роль пользователя успешно обновлена.")
    return redirect(url_for('admin_panel'))

# Обработка AJAX-запроса для смены пароля пользователя
@app.route('/admin/change_password_async/<int:user_id>', methods=['POST'])
def change_password_async(user_id):
    if not is_admin():
        return jsonify({'error': 'Доступ запрещен.'}), 403

    data = request.get_json()
    new_password = data.get('password')

    if not new_password:
        return jsonify({'error': 'Пароль обязателен.'}), 400

    hashed_password = generate_password_hash(new_password, method='pbkdf2:sha256', salt_length=16)

    conn = get_db_connection()
    conn.execute('UPDATE users SET password = ? WHERE id = ?', (hashed_password, user_id))
    conn.commit()
    conn.close()

    return jsonify({'success': 'Пароль успешно изменен.'})

# Удаление пользователя
@app.route('/admin/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    if not is_admin():
        flash("Доступ запрещен.")
        return redirect(url_for('index'))

    conn = get_db_connection()
    conn.execute('DELETE FROM users WHERE id = ?', (user_id,))
    conn.commit()
    conn.close()
    flash("Пользователь успешно удален.")
    return redirect(url_for('admin_panel'))


# Регистрация пользователя
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        # Проверка совпадения паролей на сервере
        if password != confirm_password:
            flash('Пароли не совпадают.')
            return redirect(url_for('register'))

        # Хешируем пароль и добавляем пользователя в базу данных
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256', salt_length=16)
        conn = get_db_connection()
        try:
            conn.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
            conn.commit()
            flash("Регистрация успешна. Пожалуйста, войдите.")
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash("Имя пользователя уже существует.")
        finally:
            conn.close()

    return render_template('register.html')

# Вход пользователя
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        auth_type = request.form.get('auth_type')
        username = request.form['username']
        password = request.form['password']

        if auth_type == 'ldap' and ldap_authenticate(username, password):
            session['username'] = username
            session['user_type'] = 'ldap'
            session['user_id'] = username  # Уникальный идентификатор LDAP пользователя
            session['is_admin'] = 0  # LDAP пользователи не администраторы
            return redirect(url_for('index'))
        elif auth_type == 'local':
            conn = get_db_connection()
            user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
            conn.close()
            if user and check_password_hash(user['password'], password):
                session['username'] = username
                session['user_type'] = 'local'
                session['user_id'] = user['id']
                session['is_admin'] = user['is_admin']
                return redirect(url_for('index'))
        flash("Неверные учетные данные.")
    return render_template('login.html')

#Выход
@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/get_project_data/<int:project_id>', methods=['GET'])
def get_project_data(project_id):
    conn = get_db_connection()
    project = conn.execute('SELECT * FROM projects WHERE id = ?', (project_id,)).fetchone()
    conn.close()

    if project:
        return jsonify({
            'id': project['id'],
            'name': project['name'],
            'tasks': []  # Здесь нужно добавить логику получения задач для этого проекта
        })
    else:
        return jsonify({'error': 'Проект не найден'}), 404

#Основная страница index
@app.route('/')
def index():
    if 'username' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    user_id = session['user_id']

    # Получаем проекты, где пользователь является владельцем или участником
    projects = conn.execute('''
        SELECT * FROM projects
        WHERE owner_id = ?
        OR id IN (SELECT project_id FROM project_users WHERE user_id = ?)
    ''', (user_id, user_id)).fetchall()

    # Выбираем уникальные задачи с назначенным пользователем, чтобы исключить дубликаты
    tasks = conn.execute('''
        SELECT DISTINCT tasks.id, tasks.task_number, tasks.title, tasks.status, tasks.description,
                        tasks.due_date, tasks.project_id, tasks.parent_id,
                        u.first_name || ' ' || u.last_name AS assignee_name
        FROM tasks
        LEFT JOIN users u ON tasks.assignee_id = u.id
        WHERE tasks.project_id IN (
            SELECT id FROM projects WHERE owner_id = ?
            OR id IN (SELECT project_id FROM project_users WHERE user_id = ?)
        )
    ''', (user_id, user_id)).fetchall()

    # Фильтруем задачи по их уникальному ID, чтобы исключить дубли на уровне Python
    unique_tasks = {}
    for task in tasks:
        if task['id'] not in unique_tasks:
            unique_tasks[task['id']] = task

    # Остальная логика для загрузки пользователей, проектов и подготовки данных для шаблона
    ldap_users = conn.execute('SELECT id, username, first_name, last_name FROM users WHERE password IS NULL').fetchall()
    local_users = conn.execute('SELECT id, username FROM users WHERE password IS NOT NULL').fetchall()

    # Форматируем участников для каждого проекта
    project_users = {}
    for project in projects:
        users = conn.execute('''
            SELECT u.id, u.username, u.first_name, u.last_name, u.is_admin, pu.role
            FROM users u
            JOIN project_users pu ON u.id = pu.user_id
            WHERE pu.project_id = ?
        ''', (project['id'],)).fetchall()

        project_users[project['id']] = [
            {
                'id': user['id'],
                'username': user['username'],
                'display_name': f"{user['first_name']} {user['last_name']}" if user['first_name'] and user['last_name'] else user['username'],
                'role': user['role']
            }
            for user in users
        ]

    # Группируем задачи по проектам и статусам, используя уникальные задачи
    tasks_by_project = {}
    for task in unique_tasks.values():  # Используем только уникальные задачи
        project_id = task['project_id']
        status = task['status']
        if project_id not in tasks_by_project:
            tasks_by_project[project_id] = {'To Do': [], 'In Progress': [], 'Done': []}
        tasks_by_project[project_id][status].append(task)

    conn.close()

    return render_template(
        'index.html',
        projects=projects,
        tasks_by_project=tasks_by_project,
        project_users=project_users,
        ldap_users=ldap_users,
        local_users=local_users
    )
#Вкладка контакты
@app.route('/contacts')
def contacts():
    conn = get_db_connection()
    user_id = session['user_id']

    # Загружаем локальные контакты пользователя
    local_contacts = conn.execute('''
        SELECT u.id, u.username, u.first_name, u.last_name, u.email, u.phone, u.notes
        FROM users u
        JOIN contacts c ON u.id = c.contact_id
        WHERE c.user_id = ?
    ''', (user_id,)).fetchall()

    # Загружаем всех пользователей для глобальной книги
    all_users = conn.execute('''
        SELECT id, username, first_name, last_name, email, phone, notes FROM users
    ''').fetchall()

    conn.close()

    return render_template('contacts.html', local_contacts=local_contacts, all_users=all_users)
#Добавление контактов
@app.route('/add_contact', methods=['POST'])
def add_contact():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    contact_id = request.form['contact_id']
    user_id = session['user_id']

    conn = get_db_connection()

    # Проверяем, что контакт ещё не добавлен
    existing = conn.execute(
        'SELECT * FROM contacts WHERE user_id = ? AND contact_id = ?', (user_id, contact_id)
    ).fetchone()

    if not existing:
        conn.execute('INSERT INTO contacts (user_id, contact_id) VALUES (?, ?)', (user_id, contact_id))
        conn.commit()

    conn.close()
    return redirect(url_for('contacts'))
#Удаление контакта
@app.route('/delete_contact', methods=['POST'])
def delete_contact():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 403

    data = request.get_json()
    contact_id = data.get('contact_id')

    if not contact_id:
        return jsonify({'error': 'Missing contact_id'}), 400

    conn = get_db_connection()
    conn.execute('DELETE FROM contacts WHERE user_id = ? AND contact_id = ?', (session['user_id'], contact_id))
    conn.commit()
    conn.close()

    return jsonify({'success': True})
#Редактирование контакта
@app.route('/update_contact', methods=['POST'])
def update_contact():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 403

    user_id = session['user_id']
    contact_id = request.form.get('contact_id')

    if not contact_id:
        return jsonify({"error": "Missing contact_id"}), 400

    new_email = request.form.get('email')
    new_phone = request.form.get('phone')
    new_first_name = request.form.get('first_name')
    new_last_name = request.form.get('last_name')

    conn = get_db_connection()
    contact = conn.execute("SELECT * FROM users WHERE id = ?", (contact_id,)).fetchone()

    if not contact:
        conn.close()
        return jsonify({"error": "Contact not found"}), 404

    # Проверяем, LDAP ли это пользователь
    if contact['is_ldap_user']:
        # LDAP-пользователь может редактировать только свой email и телефон
        if int(contact_id) != user_id:
            conn.close()
            return jsonify({"error": "You can only edit your own LDAP details"}), 403

        conn.execute("UPDATE users SET email = ?, phone = ? WHERE id = ?", (new_email, new_phone, contact_id))
    else:
        # Локальные пользователи могут редактировать имя, фамилию, email и телефон
        conn.execute("UPDATE users SET first_name = ?, last_name = ?, email = ?, phone = ? WHERE id = ?",
                     (new_first_name, new_last_name, new_email, new_phone, contact_id))

    conn.commit()
    conn.close()
    return jsonify({"success": "Contact updated successfully"})
#Страница пользователя
@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    user_id = session['user_id']

    # Получаем данные пользователя
    user = conn.execute('SELECT id, first_name, last_name, email, phone, notes, is_ldap_user FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()

    if user is None:
        return redirect(url_for('index'))

    return render_template('profile.html', user=user)
#Обновление профиля
@app.route('/update_profile', methods=['POST'])
def update_profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    user_id = session['user_id']

    # Получаем данные пользователя
    user = conn.execute('SELECT is_ldap_user FROM users WHERE id = ?', (user_id,)).fetchone()

    if user is None:
        conn.close()
        return redirect(url_for('profile'))

    # Получаем данные из формы
    email = request.form['email']
    phone = request.form['phone']
    notes = request.form['notes']

    # Если пользователь локальный, позволяем изменять имя и фамилию
    if not user['is_ldap_user']:
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        conn.execute('''
            UPDATE users SET first_name = ?, last_name = ?, email = ?, phone = ?, notes = ? WHERE id = ?
        ''', (first_name, last_name, email, phone, notes, user_id))
    else:
        # LDAP пользователи могут менять только email, телефон и заметки
        conn.execute('''
            UPDATE users SET email = ?, phone = ?, notes = ? WHERE id = ?
        ''', (email, phone, notes, user_id))

    conn.commit()
    conn.close()

    return redirect(url_for('profile'))
#Создание общего проекта
@app.route('/invite_to_project/<int:project_id>', methods=['POST'])
def invite_to_project(project_id):
    if 'username' not in session:
        return redirect(url_for('login'))

    # Получаем данные из формы
    invited_username = request.form.get('username')  # Для LDAP пользователей
    invited_user_id = request.form.get('user_id')  # Для локальных пользователей

    conn = get_db_connection()

    # Проверка существования проекта
    project = conn.execute('SELECT * FROM projects WHERE id = ?', (project_id,)).fetchone()
    if not project:
        flash("Проект не найден.")
        conn.close()
        return redirect(url_for('index'))

    # Получение ID пользователя: LDAP или локальный
    if invited_username:
        invited_user = conn.execute(
            'SELECT id, is_ldap_user FROM users WHERE username = ?', (invited_username,)
        ).fetchone()
    elif invited_user_id:
        invited_user = conn.execute(
            'SELECT id, is_ldap_user FROM users WHERE id = ?', (invited_user_id,)
        ).fetchone()
    else:
        flash("Не выбран пользователь для приглашения.")
        conn.close()
        return redirect(url_for('index'))

    # Проверка наличия пользователя
    if not invited_user:
        flash("Пользователь не найден.")
        conn.close()
        return redirect(url_for('index'))

    # Проверка, состоит ли пользователь уже в проекте
    existing_user = conn.execute(
        'SELECT * FROM project_users WHERE project_id = ? AND user_id = ?',
        (project_id, invited_user['id'])
    ).fetchone()

    # Если пользователь еще не добавлен в проект
    if not existing_user:
        conn.execute(
            'INSERT INTO project_users (project_id, user_id, role) VALUES (?, ?, ?)',
            (project_id, invited_user['id'], 'member')
        )
        conn.commit()
        flash("Пользователь успешно добавлен в проект.")
    else:
        flash("Пользователь уже состоит в проекте.")

    conn.close()
    return redirect(url_for('index'))
#Создать проект
@app.route('/create_project', methods=['POST'])
def create_project():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    project_name = request.form['project_name']
    user_id = session['user_id']  # ID пользователя, создающего проект

    conn = get_db_connection()

    # Создаем проект и связываем его с пользователем
    conn.execute('INSERT INTO projects (name, owner_id) VALUES (?, ?)', (project_name, user_id))
    project_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]

    # Добавляем пользователя (LDAP или локального) в проект с ролью "owner"
    conn.execute('INSERT INTO project_users (project_id, user_id, role) VALUES (?, ?, ?)', (project_id, user_id, 'owner'))

    conn.commit()
    conn.close()

    return redirect(url_for('index'))

#Удалить пользователя из проекта
@app.route('/remove_user_from_project', methods=['POST'])
def remove_user_from_project():
    if 'username' not in session:
        return jsonify({'error': 'Вы не авторизованы'}), 403

    data = request.get_json()
    project_id = data.get('project_id')
    username = data.get('username')

    conn = get_db_connection()

    # Получаем ID пользователя, которого нужно удалить
    user_to_remove = conn.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone()
    if not user_to_remove:
        conn.close()
        return jsonify({'error': 'Пользователь не найден'}), 404

    # Проверяем, является ли текущий пользователь владельцем проекта
    project = conn.execute('SELECT owner_id FROM projects WHERE id = ?', (project_id,)).fetchone()
    if not project:
        conn.close()
        return jsonify({'error': 'Проект не найден'}), 404

    current_user_id = session['user_id']
    # Проверка, что текущий пользователь - владелец проекта
    if project['owner_id'] != current_user_id:
        conn.close()
        return jsonify({'error': 'Только владелец проекта может удалять участников'}), 403

    # Запрещаем удалять владельца проекта
    if user_to_remove['id'] == project['owner_id']:
        conn.close()
        return jsonify({'error': 'Нельзя удалить владельца проекта'}), 400

    # Удаляем участника из проекта
    conn.execute('DELETE FROM project_users WHERE project_id = ? AND user_id = ?', (project_id, user_to_remove['id']))
    conn.commit()
    conn.close()

    return jsonify({'success': 'Пользователь успешно удален из проекта'})
#Календарь
@app.route('/calendar')
def calendar_view():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    user_id = session['user_id']

    # Получаем только задачи проектов, где пользователь владелец или участник
    tasks = conn.execute('''
        SELECT tasks.* FROM tasks
        JOIN projects ON tasks.project_id = projects.id
        LEFT JOIN project_users ON projects.id = project_users.project_id
        WHERE (projects.owner_id = ? OR project_users.user_id = ?)
        AND tasks.due_date IS NOT NULL
    ''', (user_id, user_id)).fetchall()
    conn.close()

    return render_template('calendar.html', tasks=tasks)

#Маршрут для отображения задачи
@app.route('/task/<int:task_id>')
def view_task(task_id):
    conn = get_db_connection()
    task = conn.execute('SELECT * FROM tasks WHERE id = ?', (task_id,)).fetchone()
    conn.close()

    if task is None:
        return "Задача не найдена", 404

    return render_template('view_task.html', task=task)

#Добавление задачи
@app.route('/add_task', methods=['POST'])
def add_task():
    title = request.form['title']
    project_id = request.form['project_id']
    due_date = request.form.get('due_date')  # Получаем срок выполнения задачи, если он был указан
    parent_id = request.form.get('parent_id')  # Получаем родительскую задачу (если она была указана)
    assignee_id = request.form.get('assignee_id')  # Получаем ID назначенного пользователя
    user_id = session.get('user_id') if not session.get('is_ldap_user') else None

    conn = get_db_connection()

    # Получаем уникальный номер задачи
    max_task_number = conn.execute('SELECT COALESCE(MAX(task_number), 0) + 1 FROM tasks').fetchone()[0]

    # Вставляем новую задачу с уникальным task_number и назначением
    if due_date:
        conn.execute(
            '''INSERT INTO tasks (task_number, title, project_id, status, user_id, due_date, parent_id, assignee_id)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
            (max_task_number, title, project_id, 'To Do', user_id, due_date, parent_id, assignee_id))
    else:
        conn.execute(
            '''INSERT INTO tasks (task_number, title, project_id, status, user_id, parent_id, assignee_id)
               VALUES (?, ?, ?, ?, ?, ?, ?)''',
            (max_task_number, title, project_id, 'To Do', user_id, parent_id, assignee_id))

    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/update_task_title/<int:task_id>', methods=['POST'])
def update_task_title(task_id):
    data = request.get_json()
    new_title = data.get('title')
    conn = get_db_connection()
    conn.execute('UPDATE tasks SET title = ? WHERE id = ?', (new_title, task_id))
    conn.commit()
    conn.close()
    return jsonify(success=True)

@app.route('/update_task_status/<int:task_id>', methods=['POST'])
def update_task_status(task_id):
    data = request.get_json()
    status = data.get('status')
    project_id = data.get('project_id')
    conn = get_db_connection()
    conn.execute('UPDATE tasks SET status = ?, project_id = ? WHERE id = ?', (status, project_id, task_id))
    conn.commit()
    conn.close()
    return jsonify(success=True)

@app.route('/update_task_description/<int:task_id>', methods=['POST'])
def update_task_description(task_id):
    data = request.get_json()
    description = data.get('description')
    conn = get_db_connection()
    conn.execute('UPDATE tasks SET description = ? WHERE id = ?', (description, task_id))
    conn.commit()
    conn.close()
    return jsonify(success=True)

@app.route('/delete_task', methods=['POST'])
def delete_task():
    data = request.get_json()
    task_id = data.get('task_id')
    conn = get_db_connection()
    conn.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
    conn.commit()
    conn.close()
    return jsonify(success=True)

@app.route('/delete_project', methods=['POST'])
def delete_project():
    data = request.get_json()
    project_id = data.get('project_id')
    conn = get_db_connection()

    # Проверка: владелец проекта или администратор
    user_id = session['user_id']
    project = conn.execute('SELECT owner_id FROM projects WHERE id = ?', (project_id,)).fetchone()

    if project['owner_id'] == user_id or session.get('is_admin'):
        conn.execute('DELETE FROM tasks WHERE project_id = ?', (project_id,))
        conn.execute('DELETE FROM projects WHERE id = ?', (project_id,))
        conn.commit()
        conn.close()
        return jsonify(success=True)
    else:
        conn.close()
        return jsonify(error="У вас нет прав для удаления этого проекта"), 403

if __name__ == '__main__':
    init_db()
    app.run(debug=True)