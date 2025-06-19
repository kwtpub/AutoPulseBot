import os
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.tl.types import InputMediaPhoto

async def send_message_to_channel(message: str):
    load_dotenv()
    api_id = int(os.getenv("TELEGRAM_API_ID"))
    api_hash = os.getenv("TELEGRAM_API_HASH")
    phone = os.getenv("TELEGRAM_PHONE")
    channel_id = os.getenv("TELEGRAM_CHANNEL_ID")

    client = TelegramClient('session', api_id, api_hash)
    await client.start(phone=phone)
    await client.send_message(channel_id, message)
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
    load_dotenv()
    api_id = int(os.getenv("TELEGRAM_API_ID"))
    api_hash = os.getenv("TELEGRAM_API_HASH")
    phone = os.getenv("TELEGRAM_PHONE")

    client = TelegramClient('session', api_id, api_hash)
    await client.start(phone=phone)
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

async def send_message_with_photos_to_channel(message: str, photo_paths: list):
    load_dotenv()
    api_id = int(os.getenv("TELEGRAM_API_ID"))
    api_hash = os.getenv("TELEGRAM_API_HASH")
    phone = os.getenv("TELEGRAM_PHONE")
    channel_id = os.getenv("TELEGRAM_CHANNEL_ID")

    client = TelegramClient('session', api_id, api_hash)
    await client.start(phone=phone)
    # Если есть фото
    if photo_paths:
        if len(message) > 1024:
            # Сначала отправляем текст, потом фото без подписи
            await client.send_message(channel_id, message)
            await client.send_file(channel_id, photo_paths, silent=False)
        else:
            # Можно отправить как подпись к первой фотке
            await client.send_file(channel_id, photo_paths, caption=message, silent=False)
    else:
        await client.send_message(channel_id, message)
    await client.disconnect() 