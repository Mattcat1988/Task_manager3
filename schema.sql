CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password TEXT,
    is_admin INTEGER DEFAULT 0,
    first_name TEXT,  -- Имя
    last_name TEXT,   -- Фамилия
    middle_name TEXT, -- Отчество
    email TEXT DEFAULT '', -- Почта (по умолчанию пустая строка)
    phone TEXT DEFAULT '', -- Телефон (по умолчанию пустая строка)
    notes TEXT DEFAULT '', -- Запись о пользователе
    is_ldap_user INTEGER DEFAULT 0 -- LDAP-пользователь: 1 для LDAP, 0 для обычного
);

CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    owner_id INTEGER NOT NULL, -- Владелец проекта
    status TEXT DEFAULT 'Концепция' CHECK(status IN ('Концепция', 'Запущено', 'В Работе', 'Обзор', 'Завершено')), -- Статус проекта
    priority TEXT DEFAULT 'Средний' CHECK(priority IN ('Высокий', 'Средний', 'Низкий')), -- Приоритет проекта
    FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS project_users (
    project_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    role TEXT NOT NULL DEFAULT 'member', -- Роль участника (по умолчанию 'member')
    PRIMARY KEY (project_id, user_id),
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_number INTEGER UNIQUE, -- Уникальный номер задачи
    title TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('To Do', 'In Progress', 'Done')),
    description TEXT,
    due_date DATE,
    project_id INTEGER NOT NULL,
    user_id INTEGER,  -- Пользователь, который создал задачу
    parent_id INTEGER,  -- Связь для подзадач
    assignee_id INTEGER,  -- Назначенный пользователь
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (parent_id) REFERENCES tasks(id) ON DELETE CASCADE,
    FOREIGN KEY (assignee_id) REFERENCES users(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS contacts (
    user_id INTEGER NOT NULL,
    contact_id INTEGER NOT NULL,
    PRIMARY KEY (user_id, contact_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (contact_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS ldap_settings (
    id INTEGER PRIMARY KEY CHECK (id = 1) UNIQUE, -- Гарантируем, что будет только одна запись
    server TEXT NOT NULL,
    port INTEGER NOT NULL,
    bind_user TEXT NOT NULL,
    bind_password TEXT NOT NULL,
    base_dn TEXT NOT NULL,
    user_attr TEXT NOT NULL
);