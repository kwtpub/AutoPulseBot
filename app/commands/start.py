from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, CommandHandler, ConversationHandler, MessageHandler, CallbackQueryHandler, filters

LEAVE_REQUEST, = range(1)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("Оставить заявку", callback_data="leave_request")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Здравствуйте! Присылайте вашу заявку, и она будет передана менеджеру.",
        reply_markup=reply_markup
    )

async def leave_request_entry_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "Пожалуйста, опишите вашу заявку одним сообщением. После отправки мы передадим её менеджеру."
    )
    # Сохраняем id сообщения бота корректно
    context.user_data['request_prompt_message_id'] = query.message.message_id
    context.user_data['request_prompt_chat_id'] = query.message.chat_id
    return LEAVE_REQUEST

async def handle_leave_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ADMIN_GROUP_ID = context.application.bot_data['ADMIN_GROUP_ID']
    user = update.effective_user
    try:
        await update.message.forward(chat_id=ADMIN_GROUP_ID)
    except Exception:
        text = update.message.text
        forward_text = f"Новая заявка от @{user.username or user.id} (ID: {user.id}):\n\n{text}"
        await context.bot.send_message(chat_id=ADMIN_GROUP_ID, text=forward_text)
    # Редактируем предыдущее сообщение бота
    prompt_msg_id = context.user_data.get('request_prompt_message_id')
    prompt_chat_id = context.user_data.get('request_prompt_chat_id')
    if prompt_msg_id and prompt_chat_id:
        try:
            await context.bot.edit_message_text(
                chat_id=prompt_chat_id,
                message_id=prompt_msg_id,
                text="Заявка отправлена! Менеджер свяжется с вами."
            )
        except Exception:
            pass
    return -1

# Регистрируем все хендлеры заявки локально

def register_handlers(application):
    """Регистрирует все обработчики для команды start"""
    
    # Команда /start
    application.add_handler(CommandHandler("start", start))
    
    # ConversationHandler для заявок
    leave_request_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(leave_request_entry_callback, pattern="^leave_request$")],
        states={
            LEAVE_REQUEST: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_leave_request)],
        },
        fallbacks=[],
        allow_reentry=True,
        per_chat=False
    )
    application.add_handler(leave_request_conv) 