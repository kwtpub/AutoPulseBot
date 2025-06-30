import os
import asyncio
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.types import InputMediaPhoto
from telethon.tl.custom import Button

load_dotenv()

api_id = int(os.getenv("TELEGRAM_API_ID"))
api_hash = os.getenv("TELEGRAM_API_HASH")
session_string = os.getenv("TELEGRAM_SESSION_STRING", "")

if not session_string:
    raise ValueError(
        "TELEGRAM_SESSION_STRING not found in environment variables. "
        "Please run 'python generate_session.py' to generate it."
    )

async def get_client():
    """Получить подключенный Telethon клиент"""
    client = TelegramClient(StringSession(session_string), api_id, api_hash)
    if not client.is_connected():
        await client.connect()
    return client

async def get_channel_id(channel_username):
    """Получить ID канала по его username"""
    client = TelegramClient(StringSession(session_string), api_id, api_hash)
    try:
        await client.start()
        entity = await client.get_entity(channel_username)
        return entity.id
    except Exception as e:
        print(f"Ошибка получения ID канала {channel_username}: {e}")
        return None
    finally:
        await client.disconnect()

async def send_to_channel(channel_id, message, photo_path=None):
    """
    Отправить сообщение в канал
    
    Args:
        channel_id: ID канала (число)
        message: Текст сообщения
        photo_path: Путь к фото (опционально)
    
    Returns:
        Отправленное сообщение или None при ошибке
    """
    client = TelegramClient(StringSession(session_string), api_id, api_hash)
    try:
        await client.start()
        
        if photo_path and os.path.exists(photo_path):
            # Отправляем с фото
            sent_message = await client.send_file(
                channel_id,
                photo_path,
                caption=message,
                parse_mode='html'
            )
        else:
            # Отправляем только текст
            sent_message = await client.send_message(
                channel_id,
                message,
                parse_mode='html'
            )
        
        print(f"Сообщение отправлено в канал {channel_id}")
        return sent_message
        
    except Exception as e:
        print(f"Ошибка отправки в канал {channel_id}: {e}")
        return None
    finally:
        await client.disconnect()

async def get_messages_from_channel(channel_username, limit=10, start_from_id=None):
    """
    Получить сообщения из канала
    
    Args:
        channel_username: Username канала (например, @channel_name)
        limit: Количество сообщений для получения
        start_from_id: ID сообщения, с которого начинать
    
    Returns:
        Список сообщений
    """
    client = TelegramClient(StringSession(session_string), api_id, api_hash)
    try:
        await client.start()
        
        # Получаем сущность канала
        entity = await client.get_entity(channel_username)
        
        # Получаем сообщения
        messages = []
        async for message in client.iter_messages(
            entity, 
            limit=limit,
            min_id=start_from_id if start_from_id else 0
        ):
            messages.append(message)
        
        return messages
        
    except Exception as e:
        print(f"Ошибка получения сообщений из {channel_username}: {e}")
        return []
    finally:
        await client.disconnect()

# Для обратной совместимости - создаем глобальный клиент
async def get_legacy_client():
    """Создать клиент для использования с async with"""
    client = TelegramClient(StringSession(session_string), api_id, api_hash)
    return client

# Функция для получения определенного сообщения
async def get_message_by_id(channel_username, message_id):
    """Получить конкретное сообщение по ID"""
    async with TelegramClient(StringSession(session_string), api_id, api_hash) as client:
        try:
            entity = await client.get_entity(channel_username)
            message = await client.get_messages(entity, ids=message_id)
            return message
        except Exception as e:
            print(f"Ошибка получения сообщения {message_id} из {channel_username}: {e}")
            return None

async def send_message_to_channel(message: str, button_text: str = None, button_url: str = None):
    channel_id = os.getenv("TELEGRAM_CHANNEL_ID")
    
    # Поддержка как числовых ID, так и username каналов
    try:
        channel_id = int(channel_id)
    except (ValueError, TypeError):
        # Если не число, значит это username канала
        pass

    buttons = None
    if button_text and button_url:
        buttons = [
            [Button.url(button_text, button_url)]
        ]

    client = TelegramClient(StringSession(session_string), api_id, api_hash)
    await client.start()
    await client.send_message(channel_id, message, buttons=buttons)
    await client.disconnect()

def is_photo_message(msg):
    if msg.photo:
        return True
    if hasattr(msg, 'document') and msg.document and getattr(msg.document, 'mime_type', None):
        if 'image' in msg.document.mime_type:
            return True
    return False

async def fetch_text_photo_pairs(source_channel, limit=500, download_dir="downloads"):
    """
    Считывает сообщения из канала, возвращает список пар (текст, путь к фото, id).
    Пары ищутся по принципу: ближайший текст и ближайшее фото (включая документы-изображения), даже если между ними есть другие сообщения.
    Фото скачиваются с уникальным именем по id сообщения с фото.
    """
    client = TelegramClient(StringSession(session_string), api_id, api_hash)
    await client.start()
    if not os.path.exists(download_dir):
        os.makedirs(download_dir)
    # 1. Собираем все сообщения в список
    messages = []
    async for message in client.iter_messages(source_channel, limit=limit, reverse=True):
        messages.append(message)
    # Отладочный вывод
    text_count = sum(1 for m in messages if m.text and not is_photo_message(m))
    photo_count = sum(1 for m in messages if is_photo_message(m))
    print(f"Всего сообщений: {len(messages)} | С текстом: {text_count} | С фото: {photo_count}")
    used_text_ids = set()
    used_photo_ids = set()
    pairs = []
    # 2. Для каждого фото ищем ближайший неиспользованный "текст" выше по списку (всё, что не фото)
    for idx, msg in enumerate(messages):
        if is_photo_message(msg) and msg.id not in used_photo_ids:
            # Ищем "текст" выше (меньший индекс)
            text_msg = None
            for j in range(idx-1, -1, -1):
                candidate = messages[j]
                if not is_photo_message(candidate) and candidate.id not in used_text_ids:
                    text_msg = candidate
                    break
            if text_msg:
                photo_path = os.path.join(download_dir, f"photo_{msg.id}.jpg")
                await client.download_media(msg, photo_path)
                # Для универсальности, если у сообщения нет .text, берём str(candidate)
                text_content = text_msg.text if hasattr(text_msg, 'text') and text_msg.text else str(text_msg)
                pairs.append({
                    "text": text_content,
                    "photo_path": photo_path,
                    "id": msg.id
                })
                used_text_ids.add(text_msg.id)
                used_photo_ids.add(msg.id)
    print(f"Найдено пар текст+фото: {len(pairs)}")
    await client.disconnect()
    return pairs

async def send_message_with_photos_to_channel(text: str, photo_paths: list):
    """
    Отправляет пост с фотографиями и текстом в целевой канал.
    Возвращает ID созданного поста и список file_id фотографий.
    """
    target_channel = os.getenv("TARGET_CHANNEL_ID")
    
    # Поддержка как числовых ID, так и username каналов
    try:
        target_channel_id = int(target_channel)
    except (ValueError, TypeError):
        # Если не число, значит это username канала
        target_channel_id = target_channel

    # Обрезаем текст до допустимой длины подписи Telegram (1024 символа)
    max_caption_length = 1024
    if len(text) > max_caption_length:
        text = text[:max_caption_length-3] + "..."

    async with TelegramClient(StringSession(session_string), api_id, api_hash) as client:
        try:
            # Отправляем пост
            if not photo_paths:
                sent_message = await client.send_message(target_channel_id, text)
                photo_file_ids = []
            else:
                sent_message = await client.send_file(target_channel_id, photo_paths, caption=text)
                # Если это альбом, sent_message будет списком. Берем первый для ID.
                message_to_process = sent_message[0] if isinstance(sent_message, list) else sent_message
                # Извлекаем file_id для каждой фотографии
                photo_file_ids = []
                if isinstance(sent_message, list):
                    for msg in sent_message:
                        if msg.media and hasattr(msg.media, 'photo'):
                            photo_file_ids.append(msg.media.photo.id)
                elif sent_message.media and hasattr(sent_message.media, 'photo'):
                    photo_file_ids.append(sent_message.media.photo.id)
                target_message_id = message_to_process.id
            if not photo_paths:
                message_to_process = sent_message
                target_message_id = sent_message.id
            print(f">> Пост успешно отправлен в канал. ID поста: {target_message_id}")
            return target_message_id, photo_file_ids
        except Exception as e:
            print(f"❌ Ошибка при отправке сообщения в Telegram: {e}")
            return None, None 