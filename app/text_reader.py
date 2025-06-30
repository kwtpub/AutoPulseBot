import os
import asyncio
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.types import MessageService
from app.core.ocr import extract_text_from_image

load_dotenv()

api_id = int(os.getenv("TELEGRAM_API_ID"))
api_hash = os.getenv("TELEGRAM_API_HASH")
session_string = os.getenv("TELEGRAM_SESSION_STRING", "")

if not session_string:
    raise ValueError(
        "TELEGRAM_SESSION_STRING not found in environment variables. "
        "Please run 'python generate_session.py' to generate it."
    )

client = TelegramClient(StringSession(session_string), api_id, api_hash)

async def fetch_text_messages_from_channel(source_channel, limit=500):
    """
    Возвращает список обычных текстовых сообщений из канала (без вложений, не MessageService).
    [{"id": ..., "text": ...}, ...]
    """
    messages = []
    await client.start()
    async for message in client.iter_messages(source_channel, limit=limit, reverse=True):
        if (
            hasattr(message, 'text') and message.text 
            and not getattr(message, 'media', None)
            and not isinstance(message, MessageService)
        ):
            messages.append({
                "id": message.id,
                "text": message.text
            })
    await client.disconnect()
    print(f"Найдено текстовых сообщений: {len(messages)}")
    return messages

async def get_message_media(channel_username, message_id):
    """Получить медиа из сообщения"""
    await client.start()
    try:
        entity = await client.get_entity(channel_username)
        message = await client.get_messages(entity, ids=message_id)
        
        if message and message.media:
            # Скачиваем медиа файл
            media_path = await client.download_media(message.media, file='temp/')
            return media_path
        return None
    except Exception as e:
        print(f"Ошибка получения медиа: {e}")
        return None
    finally:
        await client.disconnect()

async def extract_text_from_message_media(channel_username, message_id):
    """Извлечь текст из медиа сообщения"""
    media_path = await get_message_media(channel_username, message_id)
    if media_path:
        text = await extract_text_from_image(media_path)
        # Удаляем временный файл
        if os.path.exists(media_path):
            os.remove(media_path)
        return text
    return None

if __name__ == "__main__":
    # Пример использования
    asyncio.run(extract_text_from_message_media("@your_channel", 123))