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
BUTTON_TEXT = 'Подобрать авто'
BUTTON_URL = f'https://t.me/{BOT_USERNAME}' if BOT_USERNAME else None
EXTRA_TEXT = (
    '🚗 <b>Добро пожаловать в VroomMarket!</b>\n\n'
    'Меня зовут <b>Тимофей</b>, я ваш персональный менеджер по автомобилям из Китая.\n\n'
    '🌟 Мы специализируемся на доставке популярных мировых брендов из Китая:\n\n'
    '🇩🇪 <b>НЕМЕЦКИЕ:</b> BMW • Mercedes • Audi • Volkswagen\n'
    '🇯🇵 <b>ЯПОНСКИЕ:</b> Toyota • Honda • Nissan • Mazda\n'
    '🇰🇷 <b>КОРЕЙСКИЕ:</b> Hyundai • Kia\n'
    '🇺🇸 <b>АМЕРИКАНСКИЕ:</b> Tesla • Cadillac\n\n'
    '💰 <b>Наши преимущества:</b>\n'
    '• Цены на 20-40% ниже европейских\n'
    '• Уникальные комплектации для китайского рынка\n'
    '• Полное таможенное оформление\n'
    '• Доставка в любой регион России\n\n'
    '📋 Выберите интересующий бренд или напишите ваши требования.\n\n'
    '⏰ <b>Работаем:</b> пн-вс с 9:00 до 21:00\n\n'
    'Контакты @VroomMarketManager'
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