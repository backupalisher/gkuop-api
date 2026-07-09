# Развёртывание GKUOP API на сервере (Ubuntu/Debian)

## 1. Установка зависимостей

```bash
sudo apt update && sudo apt install python3 python3-pip python3-venv git -y
```

## 2. Клонирование репозитория

```bash
mkdir -p /opt/apps && cd /opt/apps
git clone https://github.com/ВАШ_ЛОГИН/gkuop-api.git
cd gkuop-api
```

## 3. Виртуальное окружение и зависимости

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## 4. Настройка переменных окружения

Создайте файл `.env` в корне проекта:

```bash
nano .env
```

Минимальное содержимое:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=gkuop
DB_USER=gkuop_user
DB_PASSWORD=ваш_пароль
IMAP_SERVER=imap.yandex.ru
IMAP_PORT=993
IMAP_USER=ваш_email@yandex.ru
IMAP_PASSWORD=ваш_пароль_приложения
```

## 5. Запуск через systemd (рекомендуется)

Создайте файл `/etc/systemd/system/gkuop.service`:

```ini
[Unit]
Description=GKUOP API Service
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/apps/gkuop-api
ExecStart=/opt/apps/gkuop-api/.venv/bin/python3 -m uvicorn web_api.main:app --host 0.0.0.0 --port 8002
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Активируйте и запустите:

```bash
sudo systemctl daemon-reload
sudo systemctl enable gkuop --now
```

Проверка статуса:

```bash
sudo systemctl status gkuop
curl -s http://localhost:8002/tickets/410238
```

## 6. Просмотр логов

```bash
sudo journalctl -u gkuop -f
```

## 7. Обратный прокси через Nginx (опционально)

Установите Nginx:

```bash
sudo apt install nginx -y
```

Создайте конфигурацию `/etc/nginx/sites-available/gkuop`:

```nginx
server {
    listen 80;
    server_name ваш-домен.ru;

    location / {
        client_max_body_size 55m;
        proxy_pass http://127.0.0.1:8002;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
        proxy_send_timeout 120s;
    }
}
```

Активируйте сайт:

```bash
sudo ln -s /etc/nginx/sites-available/gkuop /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## 8. HTTPS через Certbot (Let's Encrypt)

```bash
sudo snap install core
sudo snap refresh core
sudo apt remove certbot -y
sudo snap install --classic certbot
sudo certbot --nginx -d ваш-домен.ru
```

## 9. Настройка файрвола

```bash
sudo ufw allow 80
sudo ufw allow 443
sudo ufw allow 8002
sudo ufw enable
```

## 10. Проверка работоспособности

```bash
# Статус сервиса
sudo systemctl status gkuop

# Прямой запрос к API
curl -s http://localhost:8002/tickets/410238

# Через Nginx (если настроен)
curl -s http://ваш-домен.ru/tickets/410238
```

## 11. Обновление кода

```bash
cd /opt/apps/gkuop-api
git pull origin main
source .venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart gkuop
```

## 12. Полезные команды

| Команда | Описание |
|---------|----------|
| `sudo systemctl start gkuop` | Запустить сервис |
| `sudo systemctl stop gkuop` | Остановить сервис |
| `sudo systemctl restart gkuop` | Перезапустить сервис |
| `sudo systemctl status gkuop` | Статус сервиса |
| `sudo journalctl -u gkuop -f` | Логи в реальном времени |
| `sudo systemctl daemon-reload` | Перечитать конфиги systemd |
