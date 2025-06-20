Отлично, вот обновлённое описание для GitHub с названием **AutoPulseBot**:

---

# 🚗 AutoPulseBot — умный бот-ретранслятор автообъявлений

**AutoPulseBot** — Telegram-бот на Python, который автоматически репостит объявления о продаже автомобилей из исходного канала в маркет-канал. Он придаёт им современное оформление, добавляет кнопки и включает встроенный менеджер для обработки заявок.

## 🔧 Возможности

* 📥 Автоматический импорт объявлений из исходного канала
* 🧼 Стильное оформление текста, фотографий и цен
* 🔘 Кнопки действия (связаться, подробнее, забронировать и т.п.)
* 👤 Встроенный менеджер:

  * Приём заявок
  * Связь с покупателями
  * Фиксация интереса и ответов
* 💬 Автоответы на часто задаваемые вопросы
* 🔐 Фильтрация контента и логирование событий

## 📦 Технологии

* **Язык:** Python 3.10+
* **Библиотека:** [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot)
* **Хранилище:** SQLite (можно заменить на PostgreSQL / MongoDB)
* **Настройки:** dotenv
* **Хостинг:** Railway / Heroku / VPS

## 🚀 Быстрый старт

```bash
git clone https://github.com/yourname/AutoPulseBot.git
cd AutoPulseBot
pip install -r requirements.txt
cp .env.example .env  # Заполни переменные окружения
python bot.py
```

## 🗂 Пример `.env`

```env

# === TELEGRAM CONFIG ===

TELEGRAM_API_ID=<ID приложения Telegram с https://my.telegram.org>  
TELEGRAM_API_HASH=<HASH ключ Telegram приложения>  
TELEGRAM_PHONE=<Телефон Telegram аккаунта, например +79991234567>  

BOT_TOKEN=<Токен бота от BotFather, например 123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11>  
BOT_USERNAME=<Username бота, например @my_bot>  
TELEGRAM_BOT_TOKEN=<Можно дублировать BOT_TOKEN, если нужно>  

TELEGRAM_CHANNEL=<Username канала, например @my_channel>  
TELEGRAM_CHANNEL_ID=<ID канала, например -1001234567890>  
CHANNEL_USERNAME=<Синоним TELEGRAM_CHANNEL_ID или username канала>  
ADMIN_GROUP_ID=<ID группы для админов, например -1009876543210>  

# === YANDEX CLOUD CONFIG ===

YANDEX_OAUTH_TOKEN=<OAuth токен, полученный в Yandex Cloud>  
YANDEX_IAM_TOKEN=<IAM токен для доступа к API Yandex>  
YANDEX_FOLDER_ID=<ID каталога в Yandex Cloud>  
YANDEX_TOKEN_TIMESTAMP=<Timestamp окончания IAM токена, например 1750418266>  

# === PERPLEXITY AI CONFIG ===

PERPLEXITY_API_KEY=<API ключ Perplexity, если используешь>  
```

## 🛠 Планы на будущее

* Веб-интерфейс для модерации и статистики
* Интеграция с базой VIN / Госномер API
* Интеллектуальная фильтрация фейков
* Рассылка новых авто по подписке

## 📬 Обратная связь

* Telegram: [@твойник](https://t.me/@kwtpubb)
* Issues: [GitHub Issues](https://github.com/yourname/AutoPulseBot/issues)

---

