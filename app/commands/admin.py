# Админ-панель и все связанные обработчики
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from app.utils.config import set_pricing_config
from app.utils.channel_parser import fetch_announcements_from_channel
import asyncio

# Эти переменные должны импортироваться из main.py или передаваться через context.application.bot_data
# ADMIN_USER_IDS, MARKUP_PERCENTAGE, SOURCE_CHANNELS, perplexity_processor

# Состояния для диалога админ-панели
SET_MARKUP, PARSER_CHANNEL, PARSER_COUNT = range(3)

async def get_admin_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Статистика", callback_data='admin_stats')],
        [InlineKeyboardButton("💰 Установить наценку %", callback_data='admin_set_markup')],
        [InlineKeyboardButton("📡 Каналы-источники", callback_data='admin_source_channels')],
        [InlineKeyboardButton("🔍 Парсер каналов", callback_data='admin_parser')],
    ])

async def get_back_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ Назад", callback_data='admin_back_to_main')]
    ])

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ADMIN_USER_IDS = context.application.bot_data['ADMIN_USER_IDS']
    user_id = update.effective_user.id
    if user_id not in ADMIN_USER_IDS:
        await update.message.reply_text("⛔️ Доступ запрещен.")
        return ConversationHandler.END
    
    reply_markup = await get_admin_keyboard()
    message = await update.message.reply_text("⚙️ Админ-панель:", reply_markup=reply_markup)
    context.user_data['admin_message_id'] = message.message_id
    return ConversationHandler.END

async def admin_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ADMIN_USER_IDS = context.application.bot_data['ADMIN_USER_IDS']
    MARKUP_PERCENTAGE = context.application.bot_data['MARKUP_PERCENTAGE']
    SOURCE_CHANNELS = context.application.bot_data['SOURCE_CHANNELS']
    query = update.callback_query
    
    # Сохраняем ID сообщения для редактирования
    context.user_data['admin_message_id'] = query.message.message_id
    
    user_id = query.from_user.id
    if user_id not in ADMIN_USER_IDS:
        await query.answer(show_alert=True, text="⛔️ Доступ запрещен.")
        return ConversationHandler.END
    
    if query.data == 'admin_stats':
        await query.answer()
        await query.edit_message_text(
            text="📊 **Статистика бота**\n\nСтатистика недоступна (отключена база данных)",
            parse_mode='Markdown',
            reply_markup=await get_admin_keyboard()
        )
        return ConversationHandler.END
        
    elif query.data == 'admin_set_markup':
        await query.answer()
        await query.edit_message_text(
            text=f"💰 **Настройка наценки**\n\nТекущая наценка: **{MARKUP_PERCENTAGE}%**\n\nВведите новое значение (например, 10 или 12.5):",
            parse_mode='Markdown'
        )
        return SET_MARKUP
        
    elif query.data == 'admin_source_channels':
        await query.answer()
        if not SOURCE_CHANNELS:
            text = "📡 **Каналы-источники**\n\nКаналы-источники не заданы.\n\n(Задаются в переменной `TELEGRAM_CHANNEL`)"
        else:
            channels_list_str = "\n".join([f"• `{ch}`" for ch in SOURCE_CHANNELS])
            text = f"📡 **Отслеживаемые каналы-источники:**\n\n{channels_list_str}\n\n(Задаются в переменной `TELEGRAM_CHANNEL`)"
        await query.edit_message_text(
            text=text,
            reply_markup=await get_back_keyboard(),
            parse_mode='Markdown'
        )
        return ConversationHandler.END
        
    elif query.data == 'admin_parser':
        await query.answer()
        await query.edit_message_text(
            text="🔍 **Парсер каналов**\n\nВведите канал для парсинга (например: @milkos44556):",
            parse_mode='Markdown'
        )
        return PARSER_CHANNEL
        
    elif query.data == 'admin_back_to_main':
        await query.answer()
        await query.edit_message_text(
            text="⚙️ Админ-панель:",
            reply_markup=await get_admin_keyboard()
        )
        return ConversationHandler.END

async def handle_set_markup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    MARKUP_PERCENTAGE = context.application.bot_data['MARKUP_PERCENTAGE']
    admin_message_id = context.user_data.get('admin_message_id')
    chat_id = update.effective_chat.id
    await update.message.delete()
    if not admin_message_id:
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
        context.application.bot_data['MARKUP_PERCENTAGE'] = new_markup
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
    admin_message_id = context.user_data.get('admin_message_id')
    chat_id = update.effective_chat.id
    await update.message.delete()
    if not admin_message_id:
        await context.bot.send_message(chat_id=chat_id, text="Не удалось найти сообщение для редактирования. Пожалуйста, вызовите /admin снова.")
        return ConversationHandler.END
    channel = update.message.text.strip()
    if not channel.startswith('@') and not channel.startswith('https://t.me/'):
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=admin_message_id,
            text="❌ Неверный формат канала. Используйте @username или https://t.me/username\n\nПопробуйте снова:",
            reply_markup=await get_back_keyboard()
        )
        return PARSER_CHANNEL
    context.user_data['parser_channel'] = channel
    await context.bot.edit_message_text(
        chat_id=chat_id,
        message_id=admin_message_id,
        text=f"🔍 **Парсер каналов**\n\nКанал: `{channel}`\n\nВведите количество последних сообщений для парсинга (например: 100):",
        parse_mode='Markdown',
        reply_markup=await get_back_keyboard()
    )
    return PARSER_COUNT

async def handle_parser_count(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admin_message_id = context.user_data.get('admin_message_id')
    chat_id = update.effective_chat.id
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
    await context.bot.edit_message_text(
        chat_id=chat_id,
        message_id=admin_message_id,
        text=f"🔍 **Запуск парсинга...**\n\nКанал: `{channel}`\nКоличество: {count} сообщений\n\n⏳ Обрабатываю...",
        parse_mode='Markdown',
        reply_markup=await get_back_keyboard()
    )
    try:
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
    perplexity_processor = context.application.bot_data['perplexity_processor']
    MARKUP_PERCENTAGE = context.application.bot_data['MARKUP_PERCENTAGE']
    try:
        announcements = await fetch_announcements_from_channel(channel, limit=count)
        if not announcements:
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=f"🔍 **Результат парсинга**\n\nКанал: `{channel}`\nНайдено объявлений: 0\n\nℹ️ Объявления не найдены или канал недоступен.",
                parse_mode='Markdown',
                reply_markup=await get_admin_keyboard()
            )
            return
        processed_count = 0
        for announcement in announcements:
            try:
                await context.application.bot_data['process_single_announcement'](
                    ann=announcement,
                    perplexity_processor=perplexity_processor,
                    source_channel=channel,
                    markup_percentage=MARKUP_PERCENTAGE
                )
                processed_count += 1
            except Exception as e:
                print(f"Ошибка обработки объявления: {e}")
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=f"✅ **Парсинг завершен!**\n\nКанал: `{channel}`\nНайдено объявлений: {len(announcements)}\nОбработано успешно: {processed_count}\n\n🚗 Объявления добавлены в каталог.",
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

async def cancel_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ADMIN_USER_IDS = context.application.bot_data['ADMIN_USER_IDS']
    user_id = update.effective_user.id
    if user_id not in ADMIN_USER_IDS:
        await update.message.reply_text("⛔️ Доступ запрещен.")
        return ConversationHandler.END
    await update.message.reply_text("❌ Операция отменена.")
    return ConversationHandler.END

def register_admin_handlers(application):
    """Регистрирует все обработчики для админ-панели"""
    
    # ConversationHandler для админ-панели
    admin_conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("admin", admin_panel),
            CallbackQueryHandler(admin_callbacks, pattern="^admin_")
        ],
        states={
            SET_MARKUP: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_set_markup)],
            PARSER_CHANNEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_parser_channel)],
            PARSER_COUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_parser_count)],
        },
        fallbacks=[CommandHandler("cancel", cancel_conversation)],
        allow_reentry=True,
        per_chat=False
    )
    
    application.add_handler(admin_conv_handler) 