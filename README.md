# 🚗 Telegram Auto Post Bot

**Telegram Auto Post Bot** — это многофункциональный Telegram-бот на Python, предназначенный для автоматизации работы с объявлениями о продаже автомобилей. Он способен парсить сообщения из одного канала, обрабатывать их с помощью AI и публиковать в другом, а также служить ботом для приёма заявок от клиентов.

## 🔧 Возможности

*   **Автоматический парсинг**: Забирает объявления (текст и фото) из указанного Telegram-канала.
*   **Распознавание текста (OCR)**: Извлекает информацию из изображений с помощью Yandex Vision.
*   **AI-обработка**: Использует Perplexity AI для создания качественных и структурированных продающих текстов на основе собранных данных.
*   **Автопостинг**: Публикует готовые, отформатированные объявления с фотографиями в целевой канал.
*   **Бот для заявок**: Работает как клиентский бот, принимая сообщения от пользователей и пересылая их в группу администраторов для дальнейшей обработки.
*   **База данных**: Сохраняет все входящие заявки в локальную базу данных SQLite.

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

## 🚀 Быстрый старт

1.  **Клонируйте репозиторий:**
    ```bash
    git clone https://github.com/ваш-логин/Telegram-Auto-Post-Bot.git
    cd Telegram-Auto-Post-Bot
    ```

2.  **Установите зависимости:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Настройте конфигурацию:**
    *   Скопируйте `example.env` в `.env` и `config.example.ini` в `config.ini`.
    *   Заполните все необходимые переменные в обоих файлах (`.env` и `config.ini`).

4.  **Запуск компонентов:**
    *   **Для автопостинга из канала в канал:**
        ```bash
        python main.py
        ```
    *   **Для запуска бота-приёмщика заявок:**
        ```bash
        python bot.py
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

## 📬 Обратная связь

*   Если у вас есть вопросы или предложения, создавайте **Issues** в этом репозитории.

---

