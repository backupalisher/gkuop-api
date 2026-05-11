"""
Скрипт для генерации AUTH_SECRET_KEY для подписи токенов.

Использование:
    python scripts/generate_hash.py

Скрипт генерирует случайный 64-символьный hex-ключ для HMAC-SHA256 подписи токенов.
"""
import secrets


def main():
    print("=" * 60)
    print("ГЕНЕРАЦИЯ AUTH_SECRET_KEY")
    print("=" * 60)
    print()
    print("Скопируйте эту строку в файл .env:")
    print()
    key = secrets.token_hex(32)
    print(f"AUTH_SECRET_KEY={key}")
    print()
    print("=" * 60)
    print("Внимание: при смене ключа все существующие токены станут невалидными.")
    print("=" * 60)


if __name__ == "__main__":
    main()
