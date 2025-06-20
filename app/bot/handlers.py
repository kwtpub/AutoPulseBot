import os
import logging
from telegram import Update
from telegram.ext import ContextTypes
from .database import save_application

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Получаем ID админской группы из переменных окружения
ADMIN_GROUP_ID = os.getenv("ADMIN_GROUP_ID")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отправляет приветственное сообщение при старте бота."""
    user = update.effective_user
    welcome_text = (
        f"Здравствуйте, {user.first_name}!\n\n"
        "Вы можете оставить заявку на подбор автомобиля или задать любой вопрос.\n\n"
        "Просто опишите, что вас интересует, и мы свяжемся с вами в ближайшее время."
    )
    await update.message.reply_text(welcome_text)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает текстовые сообщения от пользователя, сохраняет и пересылает их."""
    user = update.effective_user
    text = update.message.text

    # 1. Сохраняем заявку в базу данных
    try:
        save_application(user.id, user.username or user.first_name, text)
        logger.info(f"Сохранена заявка от пользователя {user.id} ({user.username})")
    except Exception as e:
        logger.error(f"Ошибка при сохранении заявки от {user.id}: {e}")
        # Можно отправить сообщение об ошибке пользователю, если это необходимо
        # await update.message.reply_text("Произошла ошибка при сохранении вашей заявки. Пожалуйста, попробуйте еще раз.")
        # return

    # 2. Пересылаем сообщение в админский чат
    if ADMIN_GROUP_ID:
        try:
            # Формируем сообщение для админов
            admin_message = (
                f"Новая заявка от пользователя {user.first_name} (@{user.username}, ID: {user.id})\n"
                f"-------------------\n"
                f"{text}"
            )
            await context.bot.send_message(chat_id=ADMIN_GROUP_ID, text=admin_message)
            logger.info(f"Заявка от {user.id} переслана в группу {ADMIN_GROUP_ID}")
        except Exception as e:
            logger.error(f"Ошибка при пересылке сообщения в группу {ADMIN_GROUP_ID}: {e}")
            # Здесь можно добавить логику уведомления, если пересылка не удалась
    else:
        logger.warning("Переменная окружения ADMIN_GROUP_ID не установлена. Пересылка отключена.")

    # 3. Отправляем подтверждение пользователю
    confirmation_text = "Спасибо за ваше обращение! Мы получили вашу заявку и скоро свяжемся с вами."
    await update.message.reply_text(confirmation_text)
