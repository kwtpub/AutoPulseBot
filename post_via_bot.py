import os
import asyncio
from dotenv import load_dotenv
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup

# Загрузка переменных окружения
load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHANNEL_USERNAME = os.getenv('CHANNEL_USERNAME')  # Например, @yourchannel
BOT_USERNAME = os.getenv('BOT_USERNAME')

# Текст для кнопки и пояснения
BUTTON_TEXT = 'Оставить заявку'
BUTTON_URL = f'https://t.me/{BOT_USERNAME}' if BOT_USERNAME else None
EXTRA_TEXT = (
    'Вы можете оставить заявку нажав на эту кнопку, '
    'или просто напишите сюда свои пожелания — постараемся подобрать вам машину.'
)

async def send_application_message():
    bot = Bot(token=BOT_TOKEN)
    reply_markup = None
    if BUTTON_URL:
        reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton(BUTTON_TEXT, url=BUTTON_URL)]
        ])
    await bot.send_message(
        chat_id=CHANNEL_USERNAME,
        text=EXTRA_TEXT,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

if __name__ == '__main__':
    asyncio.run(send_application_message()) 