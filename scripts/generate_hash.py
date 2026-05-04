"""
Скрипт для генерации SHA-256 хешей логина и пароля.

Использование:
    python scripts/generate_hash.py

Скрипт запросит логин и пароль, выведет готовые строки
для вставки в файл .env
"""
import hashlib


def hash_string(value: str) -> str:
    """Возвращает SHA-256 хеш строки"""
    return hashlib.sha256(value.encode()).hexdigest()


def main():
    print("=" * 60)
    print("ГЕНЕРАЦИЯ ХЕШЕЙ ДЛЯ .env")
    print("=" * 60)
    print()

    login = input("Введите логин: ").strip()
    if not login:
        print("Ошибка: логин не может быть пустым")
        return

    import getpass
    password = getpass.getpass("Введите пароль: ")
    if not password:
        print("Ошибка: пароль не может быть пустым")
        return

    login_hash = hash_string(login)
    password_hash = hash_string(password)

    print()
    print("=" * 60)
    print("Скопируйте эти строки в файл .env:")
    print("=" * 60)
    print()
    print(f"WEB_USER_HASH={login_hash}")
    print(f"WEB_PASSWORD_HASH={password_hash}")
    print()
    print("=" * 60)
    print(f"Хеш логина:    {login_hash}")
    print(f"Хеш пароля:    {password_hash}")
    print("=" * 60)


if __name__ == "__main__":
    main()
