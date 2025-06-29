import os
import asyncio
from dotenv import load_dotenv
from app.utils.channel_parser import fetch_announcements_from_channel
from app.core.ocr import OCRProcessor
from app.core.perplexity import PerplexityProcessor
from app.utils.message_formatter import MessageFormatter
from app.core.telegram import send_message_to_channel, send_message_with_photos_to_channel
from app.utils.config import get_telegram_config, get_pricing_config
import re
import sys
import shutil
import random
from app.bot.database import AsyncSessionLocal, Car

def extract_car_details(text: str):
    """Извлекает детали автомобиля из текста с помощью регулярных выражений."""
    details = {
        'brand': None,
        'model': None,
        'year': None,
        'price': None
    }
    
    if not text or not isinstance(text, str):
        return details
        
    title_match = re.search(r'^(.*?)\s*\[(\d{4})\]', text)
    if title_match:
        try:
            full_model_name = title_match.group(1).strip()
            brand_model_parts = full_model_name.split(' ', 1)
            details['brand'] = brand_model_parts[0]
            details['model'] = brand_model_parts[1] if len(brand_model_parts) > 1 else None
            details['year'] = int(title_match.group(2))
        except (ValueError, IndexError) as e:
            print(f"Ошибка при извлечении года из текста: {e}")
            details['year'] = None

    price_match = re.search(r'(?i)Цена:\s*([\d\s,]+)', text)
    if price_match:
        try:
            price_str = price_match.group(1).replace(' ', '').replace(',', '')
            details['price'] = float(price_str)
        except (ValueError, TypeError):
            pass
    return details

async def process_single_announcement(ann, db_session, perplexity_processor, source_channel, markup_percentage):
    """
    Обрабатывает одно объявление: OCR, Perplexity, сохранение в БД и публикация.
    """
    message_id = ann["id"]
    print(f"--- Обработка объявления ID: {message_id} ---")

    existing_car = db_session.query(Car).filter(Car.source_message_id == message_id).first()
    if existing_car:
        print(f">> Объявление с ID {message_id} уже есть в базе. Пропускаем.")
        if ann.get("photos"):
            photo_dir = os.path.dirname(ann["photos"][0])
            if os.path.exists(photo_dir):
                shutil.rmtree(photo_dir)
        return

    custom_id = str(random.randint(10000000, 99999999))
    while db_session.query(Car).filter(Car.custom_id == custom_id).first():
        custom_id = str(random.randint(10000000, 99999999))
    print(f">> Сгенерирован уникальный ID для поста: {custom_id}")
    
    ocr_texts = []
    if ann.get("photos"):
        print(f">> Запуск OCR для {len(ann['photos'])} фото...")
        ocr = OCRProcessor(lang='ru', use_yandex=True)
        for photo_path in ann["photos"]:
            ocr_text = await ocr.extract_text(photo_path)
            if ocr_text and not ocr_text.startswith('Ошибка разбора ответа'):
                ocr_texts.append(ocr_text)
        print(">> OCR завершен.")

    ocr_data = '\n'.join(ocr_texts)
    
    prompt = perplexity_processor.create_prompt(ann["text"], ocr_data, custom_id, markup_percentage)
    
    print(">> Отправка запроса в Perplexity API...")
    msg = await perplexity_processor.process_text(prompt)
    print(">> Ответ от Perplexity получен.")

    # Проверяем, что получили корректный ответ
    if not msg or not isinstance(msg, str):
        print(">> Получен некорректный ответ от Perplexity. Пропускаем объявление.")
        if ann.get("photos"):
            photo_dir = os.path.dirname(ann["photos"][0])
            if os.path.exists(photo_dir):
                shutil.rmtree(photo_dir)
        return

    # Добавляем ID в начало поста
    msg = f"ID: {custom_id}\n" + msg

    # Добавляем контактную информацию в конец поста
    msg = msg.strip() + "\n\nКонтакт: @VroomMarketManager"

    car_details = extract_car_details(msg)
    new_car = Car(
        custom_id=custom_id,
        source_message_id=message_id,
        source_channel_name=source_channel,
        brand=car_details.get('brand'),
        model=car_details.get('model'),
        year=car_details.get('year'),
        price=car_details.get('price'),
        description=msg,
        status='pending_publication'
    )
    db_session.add(new_car)
    db_session.commit()
    db_session.refresh(new_car)
    print(f">> Автомобиль предварительно сохранен в базу с ID {new_car.id} (без фото).")

    # Загрузка фото в Cloudinary и обновление записи в БД
    uploaded_photo_urls = []
    if ann.get("photos"):
        from app.core.cloudinary_uploader import upload_image_to_cloudinary # Импорт здесь, чтобы избежать циклической зависимости на старте

        # Генерируем уникальный префикс для public_id на основе custom_id автомобиля
        # чтобы фото одного объявления были сгруппированы в Cloudinary
        cloudinary_public_id_prefix = f"car_{custom_id}"

        for i, photo_path in enumerate(ann["photos"]):
            # Создаем уникальный public_id для каждого фото
            # Пример: car_12345678_photo_0, car_12345678_photo_1
            photo_public_id = f"{cloudinary_public_id_prefix}_photo_{i}"

            upload_result = upload_image_to_cloudinary(photo_path, public_id=photo_public_id)
            if upload_result and upload_result.get("secure_url"):
                uploaded_photo_urls.append(upload_result.get("secure_url"))
            else:
                print(f"Не удалось загрузить фото {photo_path} в Cloudinary.")

        if uploaded_photo_urls:
            new_car.photos = uploaded_photo_urls # Сохраняем список URL-ов
            db_session.commit()
            print(f">> URL фото из Cloudinary ({len(uploaded_photo_urls)} шт.) сохранены в БД.")
        else:
            print(">> Не удалось загрузить ни одного фото в Cloudinary для этого объявления.")
            # Решаем, что делать дальше: удалить запись, оставить без фото, или пометить как ошибку
            # Пока оставим без фото, но можно добавить другую логику

    # Отправка сообщения в Telegram канал
    # Если фото были загружены в Cloudinary, используем их URL для отображения (если это поддерживается функцией отправки)
    # или отправляем только текст, если фото не критичны для отображения в Telegram напрямую.
    # В данном случае, send_message_with_photos_to_channel ожидает локальные пути.
    # Мы можем либо изменить эту функцию, чтобы она принимала URL, либо отправлять фото как раньше,
    # а Cloudinary использовать как основное хранилище.
    # Пока оставим отправку локальных фото, если они есть.

    # Важно: photo_ids, возвращаемые send_message_with_photos_to_channel, это Telegram file_id.
    # Мы их больше не сохраняем в new_car.photos, так как там теперь URL Cloudinary.
    # Если они нужны для чего-то еще (например, для редактирования сообщения с фото),
    # то нужно решить, как их обрабатывать. Пока они не используются после сохранения.

    target_msg_id, _ = await send_message_with_photos_to_channel(msg, ann["photos"]) # photo_ids больше не присваиваем

    if target_msg_id:
        new_car.target_channel_message_id = target_msg_id
        new_car.status = 'available' # Статус 'available' даже если фото не загрузились в Cloudinary, но пост опубликован
        db_session.commit()
        print(f">> Пост опубликован в Telegram. Запись в БД обновлена (статус, ID сообщения).")
    else:
        print(">> Публикация в Telegram не удалась. Откат основных данных автомобиля.")
        # Здесь важно решить, нужно ли удалять уже загруженные в Cloudinary фото, если публикация в Telegram не удалась.
        # Это зависит от требований. Пока мы их не удаляем.
        db_session.delete(new_car) # Удаляем запись о машине, если она не опубликована в Telegram
        db_session.commit()
    
    # Удаление временных локальных файлов фотографий после обработки
    if ann.get("temp_dir") and os.path.exists(ann["temp_dir"]):
        shutil.rmtree(ann["temp_dir"])
        print(f">> Временная папка {ann['temp_dir']} удалена.")
    elif ann.get("photos"): # Если temp_dir не был предоставлен, но фото есть
        # Пытаемся удалить родительскую папку первого фото, если она существует и не является корневой download_dir
        # Это более хрупкая логика, лучше передавать temp_dir из fetch_announcements_from_channel
        try:
            photo_dir = os.path.dirname(ann["photos"][0])
            # Проверяем, что это не сама папка 'downloads', чтобы случайно не удалить все
            if os.path.exists(photo_dir) and photo_dir != "downloads" and photo_dir != os.path.abspath("downloads"):
                 # Дополнительная проверка, чтобы не удалить что-то важное, если структура неожиданная
                if "temp" in photo_dir or str(message_id) in photo_dir : # Убедимся, что это похоже на временную папку
                    shutil.rmtree(photo_dir)
                    print(f">> Временная папка с фото {photo_dir} удалена (определена по пути к фото).")
        except Exception as e:
            print(f"Ошибка при попытке удаления временной папки с фото: {e}")


async def process_all_cars_from_channel():
    print(">>> Запуск конвейера обработки автомобилей...")
    load_dotenv()
    async with AsyncSessionLocal() as db:
        try:
            source_channel = os.getenv("TELEGRAM_CHANNEL")
            if not source_channel:
                print("TELEGRAM_CHANNEL не задан в .env")
                return

            limit, start_from_id = get_telegram_config()
            markup_percentage = get_pricing_config()
            print(f">>> Получение объявлений из канала {source_channel}...")
            announcements = await fetch_announcements_from_channel(source_channel, limit=limit, start_from_id=start_from_id)
            print(f">>> Получено {len(announcements)} объявлений.")

            api_key = os.getenv("PERPLEXITY_API_KEY")
            if not api_key:
                print("PERPLEXITY_API_KEY не найден в .env")
                return
            perplexity = PerplexityProcessor(api_key)

            for ann in announcements:
                await process_single_announcement(ann, db, perplexity, source_channel, markup_percentage)
        finally:
            await db.close()
            print(">>> Конвейер завершил работу.")

if __name__ == "__main__":
    asyncio.run(process_all_cars_from_channel()) 