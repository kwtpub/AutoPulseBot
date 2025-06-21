import os
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.tl.types import InputMediaPhoto
from telethon.tl.custom import Button

async def send_message_to_channel(message: str, button_text: str = None, button_url: str = None):
    load_dotenv()
    api_id = int(os.getenv("TELEGRAM_API_ID"))
    api_hash = os.getenv("TELEGRAM_API_HASH")
    phone = os.getenv("TELEGRAM_PHONE")
    channel_id = os.getenv("TELEGRAM_CHANNEL_ID")

    buttons = None
    if button_text and button_url:
        buttons = [
            [Button.url(button_text, button_url)]
        ]

    client = TelegramClient('session', api_id, api_hash)
    await client.start(phone=phone)
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

async def send_message_with_photos_to_channel(text: str, photo_paths: list):
    """
    Отправляет пост с фотографиями и текстом в целевой канал.
    Возвращает ID созданного поста и список file_id фотографий.
    """
    load_dotenv()
    api_id = os.getenv("TELEGRAM_API_ID")
    api_hash = os.getenv("TELEGRAM_API_HASH")
    session_name = "telegram_session"
    target_channel_id = int(os.getenv("TARGET_CHANNEL_ID"))

    async with TelegramClient(session_name, api_id, api_hash) as client:
        try:
            # Отправляем пост
            if not photo_paths:
                sent_message = await client.send_message(target_channel_id, text)
                photo_file_ids = []
            else:
                sent_message = await client.send_file(target_channel_id, photo_paths, caption=text)
                # Если это альбом, sent_message будет списком. Берем первый для ID.
                # Все фото из альбома будут сгруппированы под ID первого сообщения.
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
            
            print(f">> Пост успешно отправлен в канал. ID поста: {target_message_id}")
            return target_message_id, photo_file_ids

        except Exception as e:
            print(f"❌ Ошибка при отправке сообщения в Telegram: {e}")
            return None, None 