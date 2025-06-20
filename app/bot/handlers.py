from telegram import Update
from telegram.ext import ContextTypes

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отправляет приветственное сообщение при старте бота."""
    user = update.effective_user
    welcome_text = (
        f"Здравствуйте, {user.first_name}!\n\n"
        "Вы можете оставить заявку на подбор автомобиля или задать любой вопрос.\n\n"
        "Просто опишите, что вас интересует, и мы свяжемся с вами в ближайшее время."
    )
    await update.message.reply_text(welcome_text)
