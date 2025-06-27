import os
import asyncio
from dotenv import load_dotenv

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, 
    filters, ContextTypes, CallbackQueryHandler,
    ConversationHandler
)
#new comm
# --- Клиент для прослушивания канала ---
from telethon import TelegramClient, events

# --- Наши модули ---
from app.bot.database import init_db, save_application, SessionLocal, Car, Application as ApplicationDB
from app.utils.channel_parser import convert_telethon_message_to_announcement, fetch_announcements_from_channel
from app.pipeline import process_single_announcement
from app.core.perplexity import PerplexityProcessor
from app.utils.config import get_pricing_config, set_pricing_config

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

init_db()

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
    db_session = SessionLocal()
    try:
        announcement = await convert_telethon_message_to_announcement(event.message)
        if announcement:
            await process_single_announcement(
                ann=announcement,
                db_session=db_session,
                perplexity_processor=perplexity_processor,
                source_channel=source_channel_url, # Передаем конкретный канал
                markup_percentage=MARKUP_PERCENTAGE
            )
    except Exception as e:
        print(f"❌ Ошибка при обработке нового поста {event.message.id} из канала {source_channel_url}: {e}")
    finally:
        db_session.close()

# --- Админ-панель ---
async def get_admin_keyboard():
    """Возвращает клавиатуру админ-панели."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Статистика", callback_data='admin_stats')],
        [InlineKeyboardButton("💰 Установить наценку %", callback_data='admin_set_markup')],
        [InlineKeyboardButton("📡 Каналы-источники", callback_data='admin_source_channels')],
        [InlineKeyboardButton("🔍 Парсер каналов", callback_data='admin_parser')],
    ])

async def get_back_keyboard():
    """Возвращает клавиатуру с кнопкой 'Назад'."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ Назад", callback_data='admin_back_to_main')]
    ])

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает админ-панель, если у пользователя есть доступ."""
    user_id = update.effective_user.id
    if user_id not in ADMIN_USER_IDS:
        await update.message.reply_text("⛔️ Доступ запрещен.")
        return

    reply_markup = await get_admin_keyboard()
    message = await update.message.reply_text("⚙️ Админ-панель:", reply_markup=reply_markup)
    context.user_data['admin_message_id'] = message.message_id


async def admin_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает нажатия кнопок в админ-панели."""
    query = update.callback_query
    context.user_data['admin_message_id'] = query.message.message_id # Сохраняем ID на всякий случай

    user_id = query.from_user.id
    if user_id not in ADMIN_USER_IDS:
        await query.answer(show_alert=True, text="⛔️ Доступ запрещен.")
        return

    # Логика для статистики
    if query.data == 'admin_stats':
        await query.answer()
        db_session = SessionLocal()
        try:
            car_count = db_session.query(Car).count()
            app_count = db_session.query(ApplicationDB).count()
            stats_text = (
                f"📊 **Статистика базы данных**\n\n"
                f"🚗 Всего автомобилей в каталоге: **{car_count}**\n"
                f"📝 Всего получено заявок: **{app_count}**"
            )
            await query.edit_message_text(text=stats_text, parse_mode='Markdown', reply_markup=await get_admin_keyboard())
        except Exception as e:
            await query.edit_message_text(text=f"❌ Ошибка при получении статистики: {e}", reply_markup=await get_admin_keyboard())
        finally:
            db_session.close()

    # Логика для установки наценки
    elif query.data == 'admin_set_markup':
        await query.answer()
        await query.edit_message_text(
            text=f"Текущая наценка: **{MARKUP_PERCENTAGE}%**\n\n"
                 f"Введите новое значение (например, 10 или 12.5):",
            parse_mode='Markdown'
        )
        return SET_MARKUP

    # Логика для отображения каналов-источников
    elif query.data == 'admin_source_channels':
        await query.answer()
        
        if not SOURCE_CHANNELS:
            text = "📡 **Каналы-источники не заданы.**"
        else:
            channels_list_str = "\n".join([f"• `{ch}`" for ch in SOURCE_CHANNELS])
            text = f"📡 **Отслеживаемые каналы-источники:**\n\n{channels_list_str}\n\n" \
                   f"(Задаются в переменной `TELEGRAM_CHANNEL`)"

        await query.edit_message_text(
            text=text,
            reply_markup=await get_back_keyboard(),
            parse_mode='Markdown'
        )

    # Логика для парсера каналов
    elif query.data == 'admin_parser':
        await query.answer()
        await query.edit_message_text(
            text="🔍 **Парсер каналов**\n\n"
                 f"Введите канал для парсинга (например: @milkos44556):",
            parse_mode='Markdown',
            reply_markup=await get_back_keyboard()
        )
        return PARSER_CHANNEL

    # Логика для возврата в главное меню
    elif query.data == 'admin_back_to_main':
        await query.answer()
        await query.edit_message_text(
            text="⚙️ Админ-панель:",
            reply_markup=await get_admin_keyboard()
        )

async def handle_set_markup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает ввод нового процента наценки, редактируя исходное сообщение."""
    global MARKUP_PERCENTAGE
    
    admin_message_id = context.user_data.get('admin_message_id')
    chat_id = update.effective_chat.id
    
    # Удаляем сообщение пользователя с новым значением
    await update.message.delete()

    if not admin_message_id:
        # Резервный вариант, если что-то пошло не так
        await context.bot.send_message(chat_id=chat_id, text="Не удалось найти сообщение для редактирования. Пожалуйста, вызовите /admin снова.")
        return ConversationHandler.END

    reply_markup = await get_admin_keyboard()
    
    try:
        new_markup = float(update.message.text)
        if new_markup < 0 or new_markup > 100:
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=admin_message_id,
                text="❌ Наценка должна быть от 0 до 100%. Попробуйте снова:",
                reply_markup=reply_markup
            )
            return SET_MARKUP
        
        MARKUP_PERCENTAGE = new_markup
        set_pricing_config(new_markup)
        
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=admin_message_id,
            text=f"✅ Наценка успешно установлена: **{new_markup}%**",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        
    except ValueError:
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=admin_message_id,
            text="❌ Введите корректное число (например: 10 или 12.5):",
            reply_markup=reply_markup
        )
        return SET_MARKUP
    
    return ConversationHandler.END

async def handle_parser_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает ввод канала для парсинга."""
    admin_message_id = context.user_data.get('admin_message_id')
    chat_id = update.effective_chat.id
    
    # Удаляем сообщение пользователя
    await update.message.delete()
    
    if not admin_message_id:
        await context.bot.send_message(chat_id=chat_id, text="Не удалось найти сообщение для редактирования. Пожалуйста, вызовите /admin снова.")
        return ConversationHandler.END
    
    channel = update.message.text.strip()
    
    # Проверяем формат канала
    if not channel.startswith('@') and not channel.startswith('https://t.me/'):
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=admin_message_id,
            text="❌ Неверный формат канала. Используйте @username или https://t.me/username\n\nПопробуйте снова:",
            reply_markup=await get_back_keyboard()
        )
        return PARSER_CHANNEL
    
    # Сохраняем канал в контексте
    context.user_data['parser_channel'] = channel
    
    await context.bot.edit_message_text(
        chat_id=chat_id,
        message_id=admin_message_id,
        text=f"🔍 **Парсер каналов**\n\n"
             f"Канал: `{channel}`\n\n"
             f"Введите количество последних сообщений для парсинга (например: 100):",
        parse_mode='Markdown',
        reply_markup=await get_back_keyboard()
    )
    
    return PARSER_COUNT

async def handle_parser_count(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает ввод количества сообщений и запускает парсинг."""
    admin_message_id = context.user_data.get('admin_message_id')
    chat_id = update.effective_chat.id
    
    # Удаляем сообщение пользователя
    await update.message.delete()
    
    if not admin_message_id:
        await context.bot.send_message(chat_id=chat_id, text="Не удалось найти сообщение для редактирования. Пожалуйста, вызовите /admin снова.")
        return ConversationHandler.END
    
    try:
        count = int(update.message.text)
        if count <= 0 or count > 1000:
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=admin_message_id,
                text="❌ Количество должно быть от 1 до 1000. Попробуйте снова:",
                reply_markup=await get_back_keyboard()
            )
            return PARSER_COUNT
    except ValueError:
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=admin_message_id,
            text="❌ Введите корректное число. Попробуйте снова:",
            reply_markup=await get_back_keyboard()
        )
        return PARSER_COUNT
    
    channel = context.user_data.get('parser_channel')
    
    # Запускаем парсинг
    await context.bot.edit_message_text(
        chat_id=chat_id,
        message_id=admin_message_id,
        text=f"🔍 **Запуск парсинга...**\n\n"
             f"Канал: `{channel}`\n"
             f"Количество: {count} сообщений\n\n"
             f"⏳ Обрабатываю...",
        parse_mode='Markdown',
        reply_markup=await get_back_keyboard()
    )
    
    try:
        # Запускаем парсинг в фоне
        asyncio.create_task(run_parser_task(context, channel, count, admin_message_id, chat_id))
    except Exception as e:
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=admin_message_id,
            text=f"❌ **Ошибка запуска парсера:**\n\n{str(e)}",
            parse_mode='Markdown',
            reply_markup=await get_admin_keyboard()
        )
    
    return ConversationHandler.END

async def run_parser_task(context, channel, count, message_id, chat_id):
    """Выполняет парсинг канала в фоновом режиме."""
    db_session = SessionLocal()
    try:
        # Запускаем парсинг
        announcements = await fetch_announcements_from_channel(channel, limit=count)
        
        if not announcements:
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=f"🔍 **Результат парсинга**\n\n"
                     f"Канал: `{channel}`\n"
                     f"Найдено объявлений: 0\n\n"
                     f"ℹ️ Объявления не найдены или канал недоступен.",
                parse_mode='Markdown',
                reply_markup=await get_admin_keyboard()
            )
            return
        
        # Обрабатываем найденные объявления
        processed_count = 0
        for announcement in announcements:
            try:
                await process_single_announcement(
                    ann=announcement,
                    db_session=db_session,
                    perplexity_processor=perplexity_processor,
                    source_channel=channel,
                    markup_percentage=MARKUP_PERCENTAGE
                )
                processed_count += 1
            except Exception as e:
                print(f"Ошибка обработки объявления: {e}")
        
        # Обновляем сообщение с результатами
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=f"✅ **Парсинг завершен!**\n\n"
                 f"Канал: `{channel}`\n"
                 f"Найдено объявлений: {len(announcements)}\n"
                 f"Обработано успешно: {processed_count}\n\n"
                 f"🚗 Объявления добавлены в каталог.",
            parse_mode='Markdown',
            reply_markup=await get_admin_keyboard()
        )
        
    except Exception as e:
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=f"❌ **Ошибка парсинга:**\n\n{str(e)}",
            parse_mode='Markdown',
            reply_markup=await get_admin_keyboard()
        )
    finally:
        db_session.close()

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

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    save_application(user.id, user.username, update.message.text)
    
    forward_text = f"Новая заявка от @{user.username} (ID: {user.id}):\n\n{update.message.text}"
    await context.bot.send_message(chat_id=ADMIN_GROUP_ID, text=forward_text)
    await update.message.reply_text("Спасибо! Ваша заявка принята и передана менеджеру. Мы скоро с вами свяжемся.")

async def post_init(application: Application):
    """Действия после инициализации PTB (например, запуск клиента Telethon)."""
    if not SOURCE_CHANNELS:
        print("⚠️  Каналы-источники не указаны в .env (TELEGRAM_CHANNEL). Клиент Telethon не будет запущен.")
        return
        
    await client.start(phone=TELEGRAM_PHONE, password=TELEGRAM_PASSWORD)
    print("Клиент Telethon для прослушивания канала запущен.")
    print(f"✅ Бот запущен и слушает новые посты в каналах: {', '.join(SOURCE_CHANNELS)}")

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
        per_message=False # Важно для работы с одним сообщением
    )

    # Диалог для парсера каналов
    parser_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_callbacks, pattern='^admin_parser$')],
        states={
            PARSER_CHANNEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_parser_channel)],
            PARSER_COUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_parser_count)],
        },
        fallbacks=[CommandHandler('cancel', cancel_conversation)],
        per_message=False
    )

    application.add_handler(conv_handler)
    application.add_handler(parser_conv_handler)

    # Админ-команды
    application.add_handler(CommandHandler("admin", admin_panel))
    # Обработчик для остальных админ-коллбэков (кроме тех, что обрабатываются ConversationHandler)
    application.add_handler(CallbackQueryHandler(admin_callbacks, pattern='^admin_(stats|source_channels|back_to_main)$'))

    # Пользовательские команды
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("chatid", chatid))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Запускаем все вместе. `run_polling` блокирующий,
    # а `post_init` запустит Telethon в том же event loop.
    application.run_polling()

if __name__ == '__main__':
    main()
 
