from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

LEAVE_REQUEST, = range(1)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("Оставить заявку", callback_data="leave_request")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Здравствуйте! Присылайте вашу заявку, и она будет передана менеджеру     ыыыы.",
        reply_markup=reply_markup
    )

async def leave_request_entry_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "Пожалуйста, опишите вашу заявку одним сообщением. После отправки мы передадим её менеджеру."
    )
    return LEAVE_REQUEST

async def handle_leave_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ADMIN_GROUP_ID = context.application.bot_data['ADMIN_GROUP_ID']
    user = update.effective_user
    text = update.message.text
    forward_text = f"Новая заявка от @{user.username or user.id} (ID: {user.id}):\n\n{text}"
    await context.bot.send_message(chat_id=ADMIN_GROUP_ID, text=forward_text)
    await update.message.reply_text("Спасибо! Ваша заявка принята и передана менеджеру. Мы скоро с вами свяжемся.")
    return -1 