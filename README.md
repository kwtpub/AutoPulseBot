# 🚗 Telegram Auto Post Bot

**Telegram Auto Post Bot** — это многофункциональный Telegram-бот на Python, предназначенный для автоматизации работы с объявлениями о продаже автомобилей. Он способен парсить сообщения из одного канала, обрабатывать их с помощью AI и публиковать в другом, а также служить ботом для приёма заявок от клиентов.

## 🔧 Возможности

*   **Автоматический парсинг**: Забирает объявления (текст и фото) из указанного Telegram-канала.
*   **Распознавание текста (OCR)**: Извлекает информацию из изображений с помощью Yandex Vision.
*   **AI-обработка**: Использует Perplexity AI для создания качественных и структурированных продающих текстов на основе собранных данных.
*   **Автопостинг**: Публикует готовые, отформатированные объявления с фотографиями в целевой канал.
*   **Бот для заявок**: Работает как клиентский бот, принимая сообщения от пользователей и пересылая их в группу администраторов для дальнейшей обработки.
*   **База данных**: Сохраняет все входящие заявки в локальную базу данных SQLite.
*   **Админ-панель**: Интерактивное управление через Telegram бота.

## 📦 Технологии

*   **Язык:** Python 3.10+
*   **Telegram-библиотеки:**
    *   [Telethon](https://github.com/LonamiWebs/Telethon) — для парсинга и постинга в каналы.
    *   [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) — для создания клиентского бота-помощника.
*   **AI и OCR:**
    *   [Perplexity AI](https://www.perplexity.ai/)
    *   [Yandex Cloud API (Vision OCR)](https://cloud.yandex.ru/services/vision)
*   **Хранилище:** SQLite
*   **Настройки:** `config.ini` и `.env`
*   **CI/CD:** GitHub Actions, Docker, Docker Compose

## 🚀 Быстрый старт

### Локальная разработка

1.  **Клонируйте репозиторий:**
    ```bash
    git clone https://github.com/ваш-логин/Telegram-Auto-Post-Bot.git
    cd Telegram-Auto-Post-Bot
    ```

2.  **Установите зависимости:**
    ```bash
    make install
    # или
    pip install -r requirements.txt
    pip install -r requirements-dev.txt
    ```

3.  **Настройте конфигурацию:**
    *   Скопируйте `example.env` в `.env` и `config.example.ini` в `config.ini`.
    *   Заполните все необходимые переменные в обоих файлах (`.env` и `config.ini`).

4.  **Запуск:**
        ```bash
    make run
    # или
        python main.py
        ```

### Docker развертывание

1. **Сборка и запуск:**
    ```bash
    make docker-build
    make docker-run
    ```

2. **Просмотр логов:**
    ```bash
    make docker-logs
    ```

3. **Остановка:**
    ```bash
    make docker-stop
    ```

## 🛠 Разработка

### Команды Make

```bash
make help          # Показать все команды
make setup         # Настройка среды разработки
make test          # Запуск тестов с покрытием
make lint          # Проверка кода
make format        # Форматирование кода
make security      # Проверка безопасности
make ci            # Все проверки CI
make clean         # Очистка временных файлов
```

### Тестирование

```bash
# Запуск всех тестов
pytest tests/ -v

# Запуск с покрытием
pytest tests/ --cov=app --cov-report=html

# Запуск конкретного теста
pytest tests/test_config.py::TestConfig::test_get_pricing_config_default
```

### Линтинг и форматирование

```bash
# Проверка стиля кода
flake8 app/ main.py
black --check app/ main.py
isort --check-only app/ main.py

# Форматирование кода
black app/ main.py
isort app/ main.py
```

## 🔄 CI/CD

Проект использует GitHub Actions для автоматизации:

### Workflows

- **CI** (`ci.yml`): Тестирование, линтинг, проверка качества кода
- **Deploy** (`deploy.yml`): Автоматическое развертывание на сервер
- **Security** (`security.yml`): Проверка безопасности зависимостей

### Автоматизация

- ✅ Автоматические тесты при push/PR
- ✅ Проверка качества кода (flake8, black, isort)
- ✅ Проверка безопасности (safety, bandit)
- ✅ Автоматическое развертывание на main ветку
- ✅ Docker контейнеризация
- ✅ Systemd сервис для production

### Переменные окружения для CI/CD

Добавьте в GitHub Secrets:

        ```bash
# Telegram
BOT_TOKEN=your_bot_token
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash
PERPLEXITY_API_KEY=your_perplexity_key

# Server deployment
SERVER_HOST=your_server_ip
SERVER_USER=your_server_user
SERVER_SSH_KEY=your_private_key
SERVER_PORT=22
        ```

## 🗂 Пример `.env`

```env
# Токен вашего Telegram-бота, полученный от @BotFather
BOT_TOKEN="YOUR_TELEGRAM_BOT_TOKEN"
# Имя пользователя вашего бота (без @)
BOT_USERNAME="YOUR_BOT_USERNAME"

# ID группы/чата администраторов для пересылки заявок
# Чтобы узнать ID, можно использовать ботов типа @userinfobot
# Добавьте вашего бота в админ-группу с правами на отправку сообщений
ADMIN_GROUP_ID="YOUR_ADMIN_GROUP_CHAT_ID"

# --- Telethon API ---
# Данные для подключения через ваш аккаунт для парсинга/постинга
# Получить можно на https://my.telegram.org
TELEGRAM_API_ID="YOUR_API_ID"
TELEGRAM_API_HASH="YOUR_API_HASH"
TELEGRAM_PHONE="YOUR_PHONE_NUMBER" # в формате +79991234567

# --- Каналы ---
# Канал, откуда бот будет брать объявления
TELEGRAM_CHANNEL="SOURCE_CHANNEL_USERNAME"
# Канал, куда бот будет публиковать объявления
TELEGRAM_CHANNEL_ID="-100YOUR_TARGET_CHANNEL_ID"

# --- Ключи API ---
# Ключ для Perplexity AI
PERPLEXITY_API_KEY="YOUR_PERPLEXITY_API_KEY"

# --- Yandex Cloud ---
# OAuth-токен для обновления IAM-токена
YANDEX_OAUTH_TOKEN="YOUR_YANDEX_OAUTH_TOKEN"
# ID каталога в Yandex Cloud
YANDEX_FOLDER_ID="YOUR_YANDEX_FOLDER_ID"
```

## 🛠 Планы на будущее

* Веб-интерфейс для модерации и статистики
* Интеграция с базой VIN / Госномер API
* Интеллектуальная фильтрация фейков
* Рассылка новых авто по подписке
* Kubernetes развертывание
* Мониторинг и алерты

## 📬 Обратная связь

*   Если у вас есть вопросы или предложения, создавайте **Issues** в этом репозитории.

---

