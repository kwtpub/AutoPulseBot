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
from app.utils.send_to_node import send_car_to_node
from datetime import datetime

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

async def process_single_announcement(ann, perplexity_processor, source_channel, markup_percentage):
    """
    Обрабатывает одно объявление: OCR, Perplexity, отправка в Node.js API и публикация.
    """
    message_id = ann["id"]
    print("--- Обработка объявления ID: " + str(message_id))

    # Генерация уникального custom_id
    custom_id = str(random.randint(10000000, 99999999))
    print(">> Сгенерирован уникальный ID для поста:", custom_id)
    
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

    # Добавляем ID в начало поста
    msg = f"ID: {custom_id}\n" + msg

    # Добавляем контактную информацию в конец поста
    msg = msg.strip() + "\n\nКонтакт: @VroomMarketManager"

    car_details = extract_car_details(msg)
    uploaded_photo_urls = ann.get("photos", [])

    # Отправка сообщения в Telegram канал
    target_msg_id, _ = await send_message_with_photos_to_channel(msg, ann["photos"])

    # Формируем car_dict для Node.js API
    car_dict = {
        "custom_id": custom_id,
        "source_message_id": message_id,
        "source_channel_name": source_channel,
        "target_channel_message_id": target_msg_id,
        "brand": car_details.get('brand'),
        "model": car_details.get('model'),
        "year": car_details.get('year'),
        "price": car_details.get('price'),
        "description": msg,
        "photos": uploaded_photo_urls,
        "status": 'available' if target_msg_id else 'error',
        "created_at": datetime.utcnow().isoformat()
    }
    send_car_to_node(car_dict)

    # Удаление временных локальных файлов фотографий после обработки
    if ann.get("temp_dir") and os.path.exists(ann["temp_dir"]):
        shutil.rmtree(ann["temp_dir"])
        print(f">> Временная папка {ann['temp_dir']} удалена.")
    elif ann.get("photos"):
        try:
            photo_dir = os.path.dirname(ann["photos"][0])
            if os.path.exists(photo_dir) and photo_dir != "downloads" and photo_dir != os.path.abspath("downloads"):
                if "temp" in photo_dir or str(message_id) in photo_dir:
                    shutil.rmtree(photo_dir)
                    print(f">> Временная папка с фото {photo_dir} удалена (определена по пути к фото).")
        except Exception as e:
            print(f"Ошибка при попытке удаления временной папки с фото: {e}")

async def process_all_cars_from_channel():
    print(">>> Запуск конвейера обработки автомобилей...")
    load_dotenv()
    
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
            await process_single_announcement(ann, perplexity, source_channel, markup_percentage)
            
    except Exception as e:
        print(f"Ошибка в конвейере обработки: {e}")
    finally:
        print(">>> Конвейер завершил работу.")

if __name__ == "__main__":
    asyncio.run(process_all_cars_from_channel()) 