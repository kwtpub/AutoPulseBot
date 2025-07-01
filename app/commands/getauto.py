"""
Команда /getauto для получения информации об автомобиле по custom_id
"""
import asyncio
import aiohttp
import logging
import os
from io import BytesIO
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

# Настройки
logger = logging.getLogger(__name__)
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
    
    # Описание (сокращенное)
    if car_data.get('description'):
        # Убираем ID из начала описания для чистоты
        description = car_data['description']
        if description.startswith('ID:'):
            lines = description.split('\n')
            description = '\n'.join(lines[1:]).strip()
        
        # Ограничиваем длину описания для Telegram caption
        if len(description) > 300:
            description = description[:300] + "..."
        
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
    
    # Проверяем длину сообщения для Telegram caption (лимит 1024 символа)
    if len(message) > 1000:
        message = message[:950] + "...\n\n📞 **Контакт:** @VroomMarketManager"
    
    return message

async def getauto_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /getauto"""
    user_id = update.effective_user.id
    
    # Проверяем аргументы
    if not context.args or len(context.args) != 1:
        await update.message.reply_text(
            "❌ **Неправильное использование команды!**\n\n"
            "**Использование:** /getauto <custom_id>\n"
            "**Пример:** /getauto 023-455\n\n"
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
        # Обновляем статус: подключение к базе
        await loading_message.edit_text(
            f"🔍 Поиск автомобиля с ID: `{custom_id}`...\n"
            f"📡 Подключение к базе данных...",
            parse_mode='Markdown'
        )
        
        # Получаем данные из API
        car_data = await get_car_from_api(custom_id)
        
        # Обновляем статус: обработка данных
        await loading_message.edit_text(
            f"🔍 Поиск автомобиля с ID: `{custom_id}`...\n"
            f"✅ Данные получены\n"
            f"⚙️ Обработка информации...",
            parse_mode='Markdown'
        )
        
        if not car_data:
            await loading_message.edit_text(
                f"❌ **Автомобиль не найден**\n\n"
                f"Автомобиль с ID `{custom_id}` не найден в базе данных.\n"
                f"Проверьте правильность ID и попробуйте снова.",
                parse_mode='Markdown'
            )
            return
        
        # Форматируем сообщение
        message = format_car_message(car_data)
        
        # Получаем фотографии
        photos = car_data.get('photos', [])
        
        if photos and len(photos) > 0:
            # Обновляем статус: загрузка фото
            await loading_message.edit_text(
                f"🔍 Поиск автомобиля с ID: `{custom_id}`...\n"
                f"✅ Данные получены\n"
                f"✅ Информация обработана\n"
                f"📸 Загрузка фотографий ({len(photos)} шт.)...",
                parse_mode='Markdown'
            )
            
            # Скачиваем фотографии
            photo_files = []
            for i, photo_url in enumerate(photos[:10]):  # Максимум 10 фото
                photo_data = await download_image(photo_url)
                if photo_data:
                    photo_files.append(photo_data)
                # Небольшая задержка между скачиваниями
                if i < len(photos) - 1 and len(photos) > 1:
                    await asyncio.sleep(0.3)
            
            if photo_files:
                # Обновляем статус: отправка результата
                await loading_message.edit_text(
                    f"🔍 Поиск автомобиля с ID: `{custom_id}`...\n"
                    f"✅ Данные получены\n"
                    f"✅ Информация обработана\n"
                    f"✅ Фотографии загружены ({len(photo_files)} шт.)\n"
                    f"📤 Отправка результата...",
                    parse_mode='Markdown'
                )
                
                try:
                    if len(photo_files) == 1:
                        # Одно фото - отправляем с подписью
                        await update.message.reply_photo(
                            photo=photo_files[0],
                            caption=message,
                            parse_mode='Markdown'
                        )
                        
                        # Удаляем сообщение загрузки
                        await loading_message.delete()
                    else:
                        # Много фото - отправляем медиа-группу с подписью к первому фото
                        from telegram import InputMediaPhoto as TelegramInputMediaPhoto
                        
                        media_group = []
                        for i, photo_file in enumerate(photo_files):
                            if i == 0:
                                # К первому фото добавляем подпись
                                media_group.append(TelegramInputMediaPhoto(photo_file, caption=message, parse_mode='Markdown'))
                            else:
                                media_group.append(TelegramInputMediaPhoto(photo_file))
                        
                        # Отправляем фотографии с подписью
                        await context.bot.send_media_group(
                            chat_id=update.effective_chat.id,
                            media=media_group
                        )
                        
                        # Удаляем сообщение загрузки
                        await loading_message.delete()
                except Exception as e:
                    if "flood" in str(e).lower() or "too many requests" in str(e).lower():
                        logger.warning(f"Telegram флуд-лимит при отправке фото: {e}")
                        try:
                            # Пробуем отправить только первое фото
                            await update.message.reply_photo(
                                photo=photo_files[0],
                                caption=f"{message}\n\n⚠️ Остальные фото временно недоступны из-за ограничений Telegram",
                                parse_mode='Markdown'
                            )
                        except:
                            await update.message.reply_text(
                                f"⚠️ Фотографии временно недоступны из-за ограничений Telegram\n\n{message}",
                                parse_mode='Markdown'
                            )
                    else:
                        raise e
            else:
                # Если фото не удалось скачать, отправляем только текст
                await update.message.reply_text(
                    f"⚠️ Фотографии временно недоступны\n\n{message}",
                    parse_mode='Markdown'
                )
        else:
            # Обновляем статус: отправка без фото
            await loading_message.edit_text(
                f"🔍 Поиск автомобиля с ID: `{custom_id}`...\n"
                f"✅ Данные получены\n"
                f"✅ Информация обработана\n"
                f"⚠️ Фотографии отсутствуют\n"
                f"📤 Отправка результата...",
                parse_mode='Markdown'
            )
            
            # Нет фотографий, отправляем только текст
            await update.message.reply_text(
                message,
                parse_mode='Markdown'
            )
            
            # Удаляем сообщение загрузки
            await loading_message.delete()
        
        # Отправляем отдельное сообщение с кнопкой для связи с менеджером
        contact_message = (
            f"💬 **Заинтересовало это авто?**\n\n"
            f"Свяжитесь с нашим менеджером для получения дополнительной информации "
            f"и заказа автомобиля."
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