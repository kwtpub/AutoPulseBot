import os
import asyncio
from datetime import datetime
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument, MessageService
import logging
import shutil

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

api_id = int(os.getenv("TELEGRAM_API_ID"))
api_hash = os.getenv("TELEGRAM_API_HASH")
session_string = os.getenv("TELEGRAM_SESSION_STRING", "")

if not session_string:
    raise ValueError(
        "TELEGRAM_SESSION_STRING not found in environment variables. "
        "Please run 'python generate_session.py' to generate it."
    )

# Создаем клиент с StringSession
client = TelegramClient(StringSession(session_string), api_id, api_hash)

async def get_channel_messages(channel_username, limit=10, start_from_id=None):
    """
    Получить сообщения из канала с фотографиями
    
    Args:
        channel_username: Username канала (например, @channel_name или ссылка)
        limit: Количество сообщений для получения
        start_from_id: ID сообщения, с которого начинать (если None, то с самых новых)
    
    Returns:
        Список словарей с информацией о сообщениях:
        [
            {
                'id': int,
                'text': str,
                'date': datetime,
                'photos': [str], # пути к скачанным фото
                'has_media': bool
            },
            ...
        ]
    """
    try:
        await client.start()
        logger.info(f"Подключение к каналу: {channel_username}")
        
        # Получаем сущность канала
        entity = await client.get_entity(channel_username)
        logger.info(f"Найден канал: {entity.title}")
        
        messages = []
        message_count = 0
        
        # Итерируемся по сообщениям
        async for message in client.iter_messages(
            entity, 
            limit=limit,
            min_id=start_from_id if start_from_id else 0
        ):
            message_count += 1
            
            # Пропускаем служебные сообщения
            if not message.text and not message.media:
                continue
                
            message_data = {
                'id': message.id,
                'text': message.text or '',
                'date': message.date,
                'photos': [],
                'has_media': bool(message.media)
            }
            
            # Обрабатываем медиа
            if message.media:
                if isinstance(message.media, MessageMediaPhoto):
                    # Скачиваем фото
                    try:
                        photo_path = await client.download_media(
                            message.media, 
                            file=f"downloads/photo_{message.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
                        )
                        if photo_path:
                            message_data['photos'].append(photo_path)
                            logger.info(f"Фото скачано: {photo_path}")
                    except Exception as e:
                        logger.error(f"Ошибка скачивания фото из сообщения {message.id}: {e}")
                        
                elif isinstance(message.media, MessageMediaDocument):
                    # Проверяем, является ли документ изображением
                    if message.media.document.mime_type and message.media.document.mime_type.startswith('image/'):
                        try:
                            photo_path = await client.download_media(
                                message.media, 
                                file=f"downloads/image_{message.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                            )
                            if photo_path:
                                message_data['photos'].append(photo_path)
                                logger.info(f"Изображение скачано: {photo_path}")
                        except Exception as e:
                            logger.error(f"Ошибка скачивания изображения из сообщения {message.id}: {e}")
            
            messages.append(message_data)
            logger.info(f"Обработано сообщение {message.id}: текст={len(message_data['text'])} символов, фото={len(message_data['photos'])}")
        
        logger.info(f"Получено {len(messages)} сообщений из {message_count} проверенных")
        return messages
        
    except Exception as e:
        logger.error(f"Ошибка получения сообщений из {channel_username}: {e}")
        return []
    finally:
        await client.disconnect()

async def parse_channel(channel_username, message_count=10):
    """
    Парсинг канала - получение сообщений с медиа
    
    Args:
        channel_username: Имя канала или ссылка
        message_count: Количество сообщений для получения
    
    Returns:
        Список сообщений с медиа
    """
    logger.info(f"Начинаем парсинг канала {channel_username}, сообщений: {message_count}")
    
    # Убеждаемся что папка downloads существует
    os.makedirs('downloads', exist_ok=True)
    
    messages = await get_channel_messages(channel_username, limit=message_count)
    
    # Фильтруем сообщения с медиа
    media_messages = [msg for msg in messages if msg['has_media'] and msg['photos']]
    
    logger.info(f"Найдено {len(media_messages)} сообщений с фотографиями из {len(messages)} общих")
    
    return media_messages

if __name__ == "__main__":
    # Пример использования
    async def main():
        channel = "@your_channel"
        messages = await parse_channel(channel, 5)
        for msg in messages:
            print(f"Сообщение {msg['id']}: {msg['text'][:50]}... фото: {len(msg['photos'])}")
    
    asyncio.run(main())

def is_photo_message(msg):
    if msg.photo:
        return True
    if hasattr(msg, 'document') and msg.document and getattr(msg.document, 'mime_type', None):
        if 'image' in msg.document.mime_type:
            return True
    return False

async def fetch_announcements_from_channel(source_channel, limit=10, download_dir="downloads", temp_dir="temp", start_from_id=None):
    """
    Возвращает список объявлений: {'text': ..., 'photos': [photo_path, ...], 'temp_dir': ...}
    Сначала загружает буфер сообщений, затем обрабатывает их от старых к новым, чтобы правильно сгруппировать фото и текст.
    Возвращает `limit` самых последних объявлений.
    """
    # Используем уже созданный клиент с StringSession из модуля
    await client.start()
    if not os.path.exists(download_dir):
        os.makedirs(download_dir)
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
    
    # 1. Загружаем буфер сообщений (с запасом, т.к. в одном объявлении может быть много фото)
    messages_to_fetch = limit * 15 
    print(f"Загрузка последних {messages_to_fetch} сообщений для анализа...")
    messages = [msg async for msg in client.iter_messages(source_channel, limit=messages_to_fetch)]
    
    # 2. Разворачиваем, чтобы обрабатывать от старых к новым
    messages.reverse()

    # Если задан ID, отфильтруем более старые сообщения
    if start_from_id:
        messages = [m for m in messages if m.id >= start_from_id]

    announcements = []
    current_photos = []

    # 3. Обрабатываем сообщения в хронологическом порядке
    for msg in messages:
        if isinstance(msg, MessageService):
            continue
        
        if is_photo_message(msg):
            photo_path = os.path.join(download_dir, f"photo_{msg.id}.jpg")
            await client.download_media(msg, photo_path)
            current_photos.append(photo_path)
        elif hasattr(msg, 'text') and msg.text and not is_photo_message(msg):
            # Если есть фото, значит мы нашли текст для них - это объявление
            if current_photos:
                car_id = msg.id
                car_temp_dir = os.path.join(temp_dir, str(car_id))
                if os.path.exists(car_temp_dir):
                    shutil.rmtree(car_temp_dir)
                os.makedirs(car_temp_dir)
                
                with open(os.path.join(car_temp_dir, "text.txt"), "w", encoding="utf-8") as f:
                    f.write(msg.text)
                
                photo_paths = []
                for photo in current_photos:
                    dest = os.path.join(car_temp_dir, os.path.basename(photo))
                    shutil.copy(photo, dest)
                    photo_paths.append(dest)
                
                announcements.append({
                    "id": msg.id,
                    "text": msg.text,
                    "photos": photo_paths,
                    "temp_dir": car_temp_dir
                })
                current_photos = []  # сбрасываем для следующего объявления
    
    # 4. Берем `limit` последних найденных объявлений
    final_announcements = announcements[-limit:]

    await client.disconnect()
    print(f"Найдено и отобрано {len(final_announcements)} объявлений.")
    return final_announcements 

async def convert_telethon_message_to_announcement(message):
    """
    Преобразует объект сообщения Telethon в формат словаря 'announcement'.
    Скачивает фото во временную папку.
    """
    # Создаем уникальную временную папку для этого сообщения
    temp_dir = os.path.join('downloads', str(message.id))
    os.makedirs(temp_dir, exist_ok=True)
    
    photo_paths = []
    # Telethon может сгруппировать фото. Нужно скачать все.
    # Проверяем, есть ли у сообщения grouped_id.
    # Эта логика пока упрощена и может быть улучшена для более надежной работы с альбомами.
    try:
        if message.photo:
            photo_path = await message.download_media(file=os.path.join(temp_dir, f"{message.id}.jpg"))
            photo_paths.append(photo_path)
    except Exception as e:
        print(f"Не удалось скачать медиа для сообщения {message.id}: {e}")

    text = message.text or ""
    
    if not text and not photo_paths:
        # Если нет ни текста, ни фото, объявление бесполезно
        shutil.rmtree(temp_dir)
        return None

    return {
        "id": message.id,
        "text": text,
        "photos": photo_paths
    } 