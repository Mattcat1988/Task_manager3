from ldap3 import Server, Connection, ALL, NTLM, SUBTREE

# Параметры подключения
LDAP_SERVER = 'ldap://dc2.nso.loc'
LDAP_PORT = 389
LDAP_BASE_DN = 'DC=NSO,DC=LOC'
LDAP_BIND_USER_DN = 'CN=mfu,OU=Service Accounts,OU=IT,DC=NSO,DC=LOC'
LDAP_BIND_USER_PASSWORD = '22222222'
LDAP_USER_LOGIN_ATTR = 'sAMAccountName'

def ldap_authenticate(username, password):
    try:
        # Шаг 1: Подключаемся к LDAP-серверу под учетной записью для поиска пользователей
        server = Server(LDAP_SERVER, get_info=ALL)
        conn = Connection(server, user=LDAP_BIND_USER_DN, password=LDAP_BIND_USER_PASSWORD, auto_bind=True)

        # Шаг 2: Выполняем поиск пользователя по его sAMAccountName
        search_filter = f"({LDAP_USER_LOGIN_ATTR}={username})"
        conn.search(LDAP_BASE_DN, search_filter, search_scope=SUBTREE, attributes='cn')

        if len(conn.entries) == 0:
            print(f'Пользователь {username} не найден в LDAP.')
            return False

        # Получаем DN найденного пользователя
        user_dn = conn.entries[0].entry_dn
        print(f'Пользователь найден: {user_dn}')

        # Шаг 3: Проверяем учетные данные пользователя, выполняя bind от имени пользователя
        user_conn = Connection(server, user=user_dn, password=password)
        if user_conn.bind():
            print(f'Успешная авторизация пользователя {username}.')
            return True
        else:
            print(f'Ошибка аутентификации пользователя {username}: неверный пароль.')
            return False

    except Exception as e:
        print(f'Ошибка подключения к LDAP: {str(e)}')
        return False

if __name__ == "__main__":
    # Запрашиваем у пользователя логин и пароль
    username = input("Введите имя пользователя (sAMAccountName): ")
    password = input("Введите пароль: ")

    # Пытаемся авторизоваться через LDAP
    if ldap_authenticate(username, password):
        print("Авторизация прошла успешно.")
    else:
        print("Не удалось авторизоваться.")
