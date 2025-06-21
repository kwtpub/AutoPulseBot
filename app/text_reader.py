import os
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.tl.types import MessageService

async def fetch_text_messages_from_channel(source_channel, limit=500):
    """
    Возвращает список обычных текстовых сообщений из канала (без вложений, не MessageService).
    [{"id": ..., "text": ...}, ...]
    """
    load_dotenv()
    api_id = int(os.getenv("TELEGRAM_API_ID"))
    api_hash = os.getenv("TELEGRAM_API_HASH")
    phone = os.getenv("TELEGRAM_PHONE")

    client = TelegramClient('session', api_id, api_hash)
    await client.start(phone=phone)
    messages = []
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