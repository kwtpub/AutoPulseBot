import os
import asyncio
from dotenv import load_dotenv

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import (
    Application, CommandHandler, MessageHandler, 
    filters, ContextTypes, CallbackQueryHandler,
    ConversationHandler
)
#new comm
# --- Клиент для прослушивания канала ---
from telethon import TelegramClient, events

# --- Наши модули ---
from app.utils.channel_parser import convert_telethon_message_to_announcement, fetch_announcements_from_channel
from app.pipeline import process_single_announcement
from app.core.perplexity import PerplexityProcessor
from app.utils.config import get_pricing_config, set_pricing_config
from app.commands.start import start, leave_request_entry_callback, handle_leave_request, LEAVE_REQUEST
from app.commands.chatid import chatid
from app.commands.admin import (
    admin_panel, admin_callbacks, handle_set_markup, handle_parser_channel, handle_parser_count, cancel_conversation, SET_MARKUP, PARSER_CHANNEL, PARSER_COUNT
)

# --- Конфигурация ---
load_dotenv()

# --- ОТЛАДКА ---
print("\n--- ДЕБАГ: ЧТЕНИЕ КАНАЛОВ ---")
raw_channels_str = os.getenv("TELEGRAM_CHANNEL", "ПЕРЕМЕННАЯ TELEGRAM_CHANNEL НЕ НАЙДЕНА")
print(f"1. Сырая строка из .env: '{raw_channels_str}'")
parsed_channels_list = [channel.strip() for channel in raw_channels_str.split(',') if channel.strip()]
print(f"2. Результат после парсинга: {parsed_channels_list}")
print("--- КОНЕЦ ДЕБАГА ---\n")
# --- КОНЕЦ ОТЛАДКИ ---

# Telethon
API_ID = os.getenv("TELEGRAM_API_ID")
API_HASH = os.getenv("TELEGRAM_API_HASH")
SESSION_NAME = "telegram_session"
# Получаем список каналов из переменной окружения
SOURCE_CHANNELS_STR = os.getenv("TELEGRAM_CHANNEL", "")
SOURCE_CHANNELS = [channel.strip() for channel in SOURCE_CHANNELS_STR.split(',') if channel.strip()]

TELEGRAM_PHONE = os.getenv("TELEGRAM_PHONE")
TELEGRAM_PASSWORD = os.getenv("TELEGRAM_PASSWORD")

# Telegram Bot
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_GROUP_ID = int(os.getenv("ADMIN_GROUP_ID"))
ADMIN_USER_IDS = [int(admin_id) for admin_id in os.getenv("ADMIN_USER_IDS", "").split(',') if admin_id]


# Общие ресурсы
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")
perplexity_processor = PerplexityProcessor(PERPLEXITY_API_KEY)
MARKUP_PERCENTAGE = get_pricing_config()

# Состояния для диалога
SET_MARKUP, PARSER_CHANNEL, PARSER_COUNT = range(3)

# --- Клиент Telethon для прослушивания ---
client = TelegramClient(
    SESSION_NAME, 
    API_ID, 
    API_HASH,
    connection_retries=5,
    timeout=20
)

@client.on(events.NewMessage(chats=SOURCE_CHANNELS))
async def new_post_handler(event):
    """Обрабатывает новые посты из каналов-доноров."""
    source_channel_username = event.chat.username
    source_channel_url = f"https://t.me/{source_channel_username}"
    print(f"✅ Получен новый пост из {source_channel_url}. Начинаю обработку...")
    try:
        announcement = await convert_telethon_message_to_announcement(event.message)
        if announcement:
            await process_single_announcement(
                ann=announcement,
                perplexity_processor=perplexity_processor,
                source_channel=source_channel_url, # Передаем конкретный канал
                markup_percentage=MARKUP_PERCENTAGE
            )
    except Exception as e:
        print(f"❌ Ошибка при обработке нового поста {event.message.id} из канала {source_channel_url}: {e}")

# --- Обработчики команд бота (python-telegram-bot) ---
async def cancel_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отменяет текущий диалог и возвращает в админ-панель."""
    user_id = update.effective_user.id
    if user_id not in ADMIN_USER_IDS:
        await update.message.reply_text("⛔️ Доступ запрещен.")
        return ConversationHandler.END
    
    await update.message.reply_text("❌ Операция отменена.", reply_markup=await get_admin_keyboard())
    return ConversationHandler.END

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Здравствуйте! Присылайте вашу заявку, и она будет передана менеджеру.")

async def chatid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Возвращает ID чата для настройки конфигурации."""
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    chat_title = update.effective_chat.title or "Личный чат"
    
    await update.message.reply_text(
        f"📋 **Информация о чате:**\n\n"
        f"🆔 Chat ID: `{chat_id}`\n"
        f"📝 Тип: {chat_type}\n"
        f"📛 Название: {chat_title}",
        parse_mode='Markdown'
    )

async def post_init(application: Application):
    """Действия после инициализации PTB (например, запуск клиента Telethon)."""
    # Устанавливаем дефолтные команды бота
    await application.bot.set_my_commands([
        BotCommand("start", "Запуск бота"),
        BotCommand("admin", "Админ-панель"),
        BotCommand("chatid", "Узнать ID чата"),
        BotCommand("help", "Помощь"),
    ])
    if not SOURCE_CHANNELS:
        print("⚠️  Каналы-источники не указаны в .env (TELEGRAM_CHANNEL). Клиент Telethon не будет запущен.")
        return
    await client.start(phone=TELEGRAM_PHONE, password=TELEGRAM_PASSWORD)
    print("Клиент Telethon для прослушивания канала запущен.")
    print(f"✅ Бот запущен и слушает новые посты в каналах: {', '.join(SOURCE_CHANNELS)}")

# --- Синхронный запуск ---
def main():
    # Создаём приложение Telegram Bot
    application = Application.builder().token(BOT_TOKEN).build()
    # Прокидываем переменные для команд
    application.bot_data['ADMIN_GROUP_ID'] = ADMIN_GROUP_ID
    application.bot_data['ADMIN_USER_IDS'] = ADMIN_USER_IDS
    application.bot_data['MARKUP_PERCENTAGE'] = MARKUP_PERCENTAGE
    application.bot_data['SOURCE_CHANNELS'] = SOURCE_CHANNELS
    application.bot_data['perplexity_processor'] = perplexity_processor
    application.bot_data['process_single_announcement'] = process_single_announcement

    # --- Команды ---
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("chatid", chatid))

    # --- Оставить заявку ---
    from telegram.ext import ConversationHandler, MessageHandler, filters, CallbackQueryHandler
    leave_request_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(leave_request_entry_callback, pattern="^leave_request$")],
        states={
            LEAVE_REQUEST: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_leave_request)],
        },
        fallbacks=[],
        allow_reentry=True,
        per_message=True
    )
    application.add_handler(leave_request_conv)

    # --- Админ-панель ---
    admin_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("admin", admin_panel)],
        states={
            SET_MARKUP: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_set_markup)],
            PARSER_CHANNEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_parser_channel)],
            PARSER_COUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_parser_count)],
        },
        fallbacks=[CommandHandler("cancel", cancel_conversation)],
        allow_reentry=True,
        per_message=True
    )
    application.add_handler(admin_conv_handler)
    application.add_handler(CallbackQueryHandler(admin_callbacks))

    # Запуск бота
    application.run_polling()

if __name__ == "__main__":
    main()
 
