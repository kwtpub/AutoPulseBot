import os
import asyncio
from dotenv import load_dotenv

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- Клиент для прослушивания канала ---
from telethon import TelegramClient, events

# --- Наши модули ---
from app.bot.database import init_db, save_application, SessionLocal
from app.utils.channel_parser import convert_telethon_message_to_announcement
from app.pipeline import process_single_announcement
from app.core.perplexity import PerplexityProcessor
from app.utils.config import get_pricing_config

# --- Конфигурация ---
load_dotenv()
init_db()

# Telethon
API_ID = os.getenv("TELEGRAM_API_ID")
API_HASH = os.getenv("TELEGRAM_API_HASH")
SESSION_NAME = "telegram_session"
SOURCE_CHANNEL = os.getenv("TELEGRAM_CHANNEL")
TELEGRAM_PHONE = os.getenv("TELEGRAM_PHONE")
TELEGRAM_PASSWORD = os.getenv("TELEGRAM_PASSWORD")

# Telegram Bot
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_GROUP_ID = int(os.getenv("ADMIN_GROUP_ID"))

# Общие ресурсы
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")
perplexity_processor = PerplexityProcessor(PERPLEXITY_API_KEY)
MARKUP_PERCENTAGE = get_pricing_config()

# --- Клиент Telethon для прослушивания ---
client = TelegramClient(
    SESSION_NAME, 
    API_ID, 
    API_HASH,
    connection_retries=5,
    timeout=20
)

@client.on(events.NewMessage(chats=SOURCE_CHANNEL))
async def new_post_handler(event):
    """Обрабатывает новые посты из канала-донора."""
    print(f"✅ Получен новый пост из {SOURCE_CHANNEL}. Начинаю обработку...")
    db_session = SessionLocal()
    try:
        announcement = await convert_telethon_message_to_announcement(event.message)
        if announcement:
            await process_single_announcement(
                ann=announcement,
                db_session=db_session,
                perplexity_processor=perplexity_processor,
                source_channel=SOURCE_CHANNEL,
                markup_percentage=MARKUP_PERCENTAGE
            )
    except Exception as e:
        print(f"❌ Ошибка при обработке нового поста {event.message.id}: {e}")
    finally:
        db_session.close()

# --- Обработчики команд бота (python-telegram-bot) ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Здравствуйте! Присылайте вашу заявку, и она будет передана менеджеру.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    save_application(user.id, user.username, update.message.text)
    
    forward_text = f"Новая заявка от @{user.username} (ID: {user.id}):\n\n{update.message.text}"
    await context.bot.send_message(chat_id=ADMIN_GROUP_ID, text=forward_text)
    await update.message.reply_text("Спасибо! Ваша заявка принята и передана менеджеру. Мы скоро с вами свяжемся.")

async def post_init(application: Application):
    """Действия после инициализации PTB (например, запуск клиента Telethon)."""
    await client.start(phone=TELEGRAM_PHONE, password=TELEGRAM_PASSWORD)
    print("Клиент Telethon для прослушивания канала запущен.")
    print(f"✅ Бот запущен и слушает новые посты в канале '{SOURCE_CHANNEL}'...")

def main():
    """Запускает бота и клиент для прослушивания."""
    print("Запуск бота...")
    application = Application.builder().token(BOT_TOKEN).post_init(post_init).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Запускаем все вместе. `run_polling` блокирующий,
    # а `post_init` запустит Telethon в том же event loop.
    application.run_polling()

if __name__ == '__main__':
    main()
