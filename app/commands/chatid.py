from telegram import Update
from telegram.ext import ContextTypes

async def chatid(update: Update, context: ContextTypes.DEFAULT_TYPE):
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