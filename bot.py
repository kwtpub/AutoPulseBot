import os
from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from app.bot.database import init_db
from app.bot.handlers import start, handle_message

def main():
    """Запускает Telegram-бота."""
    load_dotenv()
    
    # Инициализируем базу данных
    init_db()

    bot_token = os.getenv("BOT_TOKEN")
    if not bot_token:
        print("Ошибка: BOT_TOKEN не найден в .env файле.")
        print("Пожалуйста, получите токен у @BotFather и добавьте его в .env.")
        return

    # Создаем приложение
    application = Application.builder().token(bot_token).build()

    # Добавляем обработчик для команды /start
    application.add_handler(CommandHandler("start", start))

    # Добавляем обработчик для всех текстовых сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Запускаем бота
    print("Бот запущен и готов к работе...")
    application.run_polling()

if __name__ == '__main__':
    main()
