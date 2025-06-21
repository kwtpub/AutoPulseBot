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

async def fetch_announcements_from_channel(source_channel, limit=10, download_dir="downloads", temp_dir="temp", start_from_id=None):
    """
    Возвращает список объявлений: {'text': ..., 'photos': [photo_path, ...], 'temp_dir': ...}
    Сначала загружает буфер сообщений, затем обрабатывает их от старых к новым, чтобы правильно сгруппировать фото и текст.
    Возвращает `limit` самых последних объявлений.
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