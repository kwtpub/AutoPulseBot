import os
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.tl.types import MessageService
import shutil

def is_photo_message(msg):
    if msg.photo:
        return True
    if hasattr(msg, 'document') and msg.document and getattr(msg.document, 'mime_type', None):
        if 'image' in msg.document.mime_type:
            return True
    return False

async def fetch_announcements_from_channel(source_channel, limit=500, download_dir="downloads", temp_dir="temp", start_from_id=None):
    """
    Возвращает список объявлений: {'text': ..., 'photos': [photo_path, ...], 'temp_dir': ...}
    Для каждого объявления создаёт папку temp/{id_машины}, куда сохраняет text.txt и фото.
    start_from_id — если задан, брать только сообщения с id >= start_from_id
    """
    load_dotenv()
    api_id = int(os.getenv("TELEGRAM_API_ID"))
    api_hash = os.getenv("TELEGRAM_API_HASH")
    phone = os.getenv("TELEGRAM_PHONE")

    client = TelegramClient('session', api_id, api_hash)
    await client.start(phone=phone)
    if not os.path.exists(download_dir):
        os.makedirs(download_dir)
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
    messages = []
    async for message in client.iter_messages(source_channel, limit=limit):
        if start_from_id is not None and message.id < start_from_id:
            continue
        messages.append(message)
    # Сортируем по id по возрастанию (от старых к новым)
    messages.sort(key=lambda m: m.id)
    announcements = []
    current_photos = []
    for msg in messages:
        if isinstance(msg, MessageService):
            continue
        if is_photo_message(msg):
            photo_path = os.path.join(download_dir, f"photo_{msg.id}.jpg")
            await client.download_media(msg, photo_path)
            current_photos.append(photo_path)
        elif hasattr(msg, 'text') and msg.text and not is_photo_message(msg):
            if current_photos:
                # Создаём temp-папку для машины
                car_id = msg.id
                car_temp_dir = os.path.join(temp_dir, str(car_id))
                if os.path.exists(car_temp_dir):
                    shutil.rmtree(car_temp_dir)
                os.makedirs(car_temp_dir)
                # Сохраняем текст
                with open(os.path.join(car_temp_dir, "text.txt"), "w", encoding="utf-8") as f:
                    f.write(msg.text)
                # Копируем фото
                photo_paths = []
                for photo in current_photos:
                    dest = os.path.join(car_temp_dir, os.path.basename(photo))
                    shutil.copy(photo, dest)
                    photo_paths.append(dest)
                announcements.append({
                    "text": msg.text,
                    "photos": photo_paths,
                    "temp_dir": car_temp_dir
                })
                current_photos = []  # сбрасываем фото после объявления
    # Не добавляем последний блок, если остались фото без текста
    await client.disconnect()
    print(f"Найдено объявлений: {len(announcements)}")
    return announcements 