"""
Команда /getauto для получения информации об автомобиле по custom_id
"""
import aiohttp
import os
from io import BytesIO
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

# Настройки Node.js API
NODE_API_URL = f"http://localhost:{os.getenv('NODE_PORT', 3001)}/api"

async def get_car_from_api(custom_id: str):
    """Получает данные автомобиля из Node.js API"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{NODE_API_URL}/cars/{custom_id}") as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 404:
                    return None
                else:
                    return None
    except Exception as e:
        print(f"❌ Ошибка подключения к API: {e}")
        return None

async def download_image(url: str) -> BytesIO:
    """Скачивает изображение по URL и возвращает BytesIO объект"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    image_data = await response.read()
                    return BytesIO(image_data)
                else:
                    return None
    except Exception as e:
        print(f"⚠️  Ошибка скачивания изображения {url}: {e}")
        return None

def format_car_message(car_data: dict) -> str:
    """Форматирует информацию об автомобиле для отправки"""
    message = f"🚗 **Информация об автомобиле**\n\n"
    
    # Основная информация
    if car_data.get('brand') and car_data.get('model'):
        message += f"**{car_data['brand']} {car_data['model']}**"
        if car_data.get('year'):
            message += f" ({car_data['year']})"
        message += "\n\n"
    
    # Цена
    if car_data.get('price'):
        try:
            price = float(car_data['price'])
            message += f"💰 **Цена:** {price:,.0f} ₽\n\n"
        except:
            message += f"💰 **Цена:** {car_data['price']}\n\n"
    
    # Описание
    if car_data.get('description'):
        # Убираем ID из начала описания для чистоты
        description = car_data['description']
        if description.startswith('ID:'):
            lines = description.split('\n')
            description = '\n'.join(lines[1:]).strip()
        message += f"📝 **Описание:**\n{description}\n\n"
    
    # Техническая информация
    message += f"🆔 **ID:** {car_data.get('custom_id', 'N/A')}\n"
    
    if car_data.get('source_channel_name'):
        message += f"📺 **Источник:** {car_data['source_channel_name']}\n"
    
    if car_data.get('status'):
        status_emoji = {
            'available': '✅',
            'sold': '❌', 
            'reserved': '⏳',
            'error': '⚠️'
        }
        emoji = status_emoji.get(car_data['status'], '❓')
        message += f"{emoji} **Статус:** {car_data['status']}\n"
    
    if car_data.get('created_at'):
        message += f"📅 **Добавлено:** {car_data['created_at'][:10]}\n"
    
    message += "\n📞 **Контакт:** @VroomMarketManager"
    
    return message

async def getauto_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /getauto"""
    user_id = update.effective_user.id
    
    # Проверяем аргументы
    if not context.args or len(context.args) != 1:
        await update.message.reply_text(
            "❌ **Неправильное использование команды!**\n\n"
            "**Использование:** /getauto <custom_id>\n"
            "**Пример:** /getauto 12345678\n\n"
            "Где custom_id - это ID автомобиля из объявления.",
            parse_mode='Markdown'
        )
        return
    
    custom_id = context.args[0]
    
    # Отправляем сообщение о поиске
    loading_message = await update.message.reply_text(
        f"🔍 Поиск автомобиля с ID: `{custom_id}`...",
        parse_mode='Markdown'
    )
    
    try:
        # Получаем данные из API
        car_data = await get_car_from_api(custom_id)
        
        if not car_data:
            await loading_message.edit_text(
                f"❌ **Автомобиль не найден**\n\n"
                f"Автомобиль с ID `{custom_id}` не найден в базе данных.\n"
                f"Проверьте правильность ID и попробуйте снова.",
                parse_mode='Markdown'
            )
            return
        
        # Удаляем сообщение о загрузке
        await loading_message.delete()
        
        # Форматируем сообщение
        message = format_car_message(car_data)
        
        # Получаем фотографии
        photos = car_data.get('photos', [])
        
        if photos and len(photos) > 0:
            # Скачиваем фотографии
            photo_files = []
            for photo_url in photos[:10]:  # Максимум 10 фото
                photo_data = await download_image(photo_url)
                if photo_data:
                    photo_files.append(photo_data)
            
            if photo_files:
                if len(photo_files) == 1:
                    # Одно фото - отправляем с подписью
                    await update.message.reply_photo(
                        photo=photo_files[0],
                        caption=message,
                        parse_mode='Markdown'
                    )
                else:
                    # Много фото - отправляем медиа-группу, потом текст
                    from telegram import InputMediaPhoto as TelegramInputMediaPhoto
                    
                    media_group = []
                    for photo_file in photo_files:
                        media_group.append(TelegramInputMediaPhoto(photo_file))
                    
                    # Отправляем фотографии
                    await context.bot.send_media_group(
                        chat_id=update.effective_chat.id,
                        media=media_group
                    )
                    
                    # Отправляем описание отдельно
                    await update.message.reply_text(
                        message,
                        parse_mode='Markdown'
                    )
            else:
                # Если фото не удалось скачать, отправляем только текст
                await update.message.reply_text(
                    f"⚠️ Фотографии временно недоступны\n\n{message}",
                    parse_mode='Markdown'
                )
        else:
            # Нет фотографий, отправляем только текст
            await update.message.reply_text(
                message,
                parse_mode='Markdown'
            )
        
        # Отправляем отдельное сообщение с кнопкой для связи с менеджером
        contact_message = (
            f"💬 **Заинтересовало это авто?**\n\n"
            f"Свяжитесь с нашим менеджером для получения дополнительной информации "
            f"и организации просмотра автомобиля."
        )
        
        # Создаем URL с pre-filled сообщением
        pre_filled_text = f"Меня заинтересовало авто под ID {custom_id}"
        manager_url = f"https://t.me/VroomMarketManager?text={pre_filled_text.replace(' ', '%20')}"
        
        keyboard = [[InlineKeyboardButton("📞 Написать менеджеру", url=manager_url)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            contact_message,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
            
    except Exception as e:
        print(f"❌ Ошибка в команде getauto: {e}")
        await loading_message.edit_text(
            "❌ **Произошла ошибка**\n\n"
            "Не удалось получить информацию об автомобиле. "
            "Попробуйте позже или обратитесь к администратору.",
            parse_mode='Markdown'
        ) 