import os
import asyncio
from dotenv import load_dotenv

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, 
    filters, ContextTypes, CallbackQueryHandler,
    ConversationHandler
)

# --- Клиент для прослушивания канала ---
from telethon import TelegramClient, events

# --- Наши модули ---
from app.bot.database import init_db, save_application, SessionLocal, Car, Application as ApplicationDB
from app.utils.channel_parser import convert_telethon_message_to_announcement
from app.pipeline import process_single_announcement
from app.core.perplexity import PerplexityProcessor
from app.utils.config import get_pricing_config, set_pricing_config

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
ADMIN_USER_IDS = [int(admin_id) for admin_id in os.getenv("ADMIN_USER_IDS", "").split(',') if admin_id]


# Общие ресурсы
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")
perplexity_processor = PerplexityProcessor(PERPLEXITY_API_KEY)
MARKUP_PERCENTAGE = get_pricing_config()

# Состояния для диалога
SET_MARKUP = range(1)

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

# --- Админ-панель ---
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает админ-панель, если у пользователя есть доступ."""
    user_id = update.effective_user.id
    if user_id not in ADMIN_USER_IDS:
        await update.message.reply_text("⛔️ Доступ запрещен.")
        return

    keyboard = [
        [InlineKeyboardButton("📊 Статистика", callback_data='admin_stats')],
        [InlineKeyboardButton("💰 Установить наценку %", callback_data='admin_set_markup')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("⚙️ Админ-панель:", reply_markup=reply_markup)

async def admin_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает нажатия кнопок в админ-панели."""
    query = update.callback_query
    await query.answer() # Обязательно, чтобы убрать "часики" на кнопке

    user_id = query.from_user.id
    if user_id not in ADMIN_USER_IDS:
        await query.edit_message_text(text="⛔️ Доступ запрещен.")
        return

    # Логика для статистики
    if query.data == 'admin_stats':
        db_session = SessionLocal()
        try:
            car_count = db_session.query(Car).count()
            app_count = db_session.query(ApplicationDB).count()
            stats_text = (
                f"📊 **Статистика базы данных**\n\n"
                f"🚗 Всего автомобилей в каталоге: **{car_count}**\n"
                f"📝 Всего получено заявок: **{app_count}**"
            )
            await query.edit_message_text(text=stats_text, parse_mode='Markdown')
        except Exception as e:
            await query.edit_message_text(text=f"❌ Ошибка при получении статистики: {e}")
        finally:
            db_session.close()

    # Логика для установки наценки (входит в ConversationHandler, но сам коллбэк здесь)
    elif query.data == 'admin_set_markup':
        await query.answer(text="Введите новое значение наценки в чат.", show_alert=True)
        await query.edit_message_text(
            text=f"Текущая наценка: **{MARKUP_PERCENTAGE}%**\n\n"
                 f"⬇️ Введите новое значение ниже и отправьте его сообщением.",
            parse_mode='Markdown'
        )
        return SET_MARKUP

async def handle_set_markup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает ввод нового процента наценки."""
    global MARKUP_PERCENTAGE
    user_id = update.effective_user.id
    if user_id not in ADMIN_USER_IDS:
        await update.message.reply_text("⛔️ Доступ запрещен.")
        return ConversationHandler.END

    try:
        new_markup = float(update.message.text.replace(',', '.'))
        set_pricing_config(new_markup)
        MARKUP_PERCENTAGE = new_markup
        await update.message.reply_text(f"✅ Наценка успешно изменена на {new_markup}%.")
    except ValueError:
        await update.message.reply_text("❌ Ошибка. Пожалуйста, введите число (например, 10 или 12.5).")
    except Exception as e:
        await update.message.reply_text(f"❌ Произошла ошибка при сохранении: {e}")

    return ConversationHandler.END

async def cancel_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отменяет текущий диалог."""
    await update.message.reply_text("Действие отменено.")
    return ConversationHandler.END

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

    # Диалог для установки наценки
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_callbacks, pattern='^admin_set_markup$')],
        states={
            SET_MARKUP: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_set_markup)],
        },
        fallbacks=[CommandHandler('cancel', cancel_conversation)],
    )

    application.add_handler(conv_handler)

    # Админ-команды
    application.add_handler(CommandHandler("admin", admin_panel))
    application.add_handler(CallbackQueryHandler(admin_callbacks, pattern='^admin_stats$')) # Статистика отдельно

    # Пользовательские команды
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Запускаем все вместе. `run_polling` блокирующий,
    # а `post_init` запустит Telethon в том же event loop.
    application.run_polling()

if __name__ == '__main__':
    main()
