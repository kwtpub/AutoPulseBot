import os
import asyncio
from dotenv import load_dotenv
from app.utils.channel_parser import fetch_announcements_from_channel
from app.core.ocr import OCRProcessor
from app.core.perplexity import PerplexityProcessor
from app.core.cloudinary_uploader import upload_image_to_cloudinary, get_image_url_from_cloudinary
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
    
    print(f">> Извлечение данных из текста: {text[:200]}...")
    
    # Паттерн 1: [Марка] [Модель] [Год] - формат Perplexity
    pattern1 = re.search(r'\[([^\]]+)\]\s*\[([^\]]+)\]\s*\[(\d{4})\]', text)
    if pattern1:
        details['brand'] = pattern1.group(1).strip()
        details['model'] = pattern1.group(2).strip()
        try:
            details['year'] = int(pattern1.group(3))
        except ValueError:
            pass
        print(f">> Найдено (паттерн 1): {details['brand']} {details['model']} {details['year']}")
    
    # Паттерн 2: Brand Model [Year] - оригинальный формат
    if not details['brand']:
        pattern2 = re.search(r'^(.*?)\s*\[(\d{4})\]', text)
        if pattern2:
            try:
                full_model_name = pattern2.group(1).strip()
                brand_model_parts = full_model_name.split(' ', 1)
                details['brand'] = brand_model_parts[0]
                details['model'] = brand_model_parts[1] if len(brand_model_parts) > 1 else None
                details['year'] = int(pattern2.group(2))
                print(f">> Найдено (паттерн 2): {details['brand']} {details['model']} {details['year']}")
            except (ValueError, IndexError) as e:
                print(f"Ошибка при извлечении года из текста: {e}")
    
    # Паттерн 3: Поиск в начале строки "Марка Модель Год"
    if not details['brand']:
        lines = text.split('\n')
        for line in lines[:3]:  # проверяем первые 3 строки
            line = line.strip()
            if line and not line.startswith('ID:'):
                # Ищем год в строке
                year_match = re.search(r'\b(19|20)\d{2}\b', line)
                if year_match:
                    year = int(year_match.group())
                    # Берем часть строки до года
                    before_year = line[:year_match.start()].strip()
                    # Убираем лишние символы
                    before_year = re.sub(r'[^\w\s]', ' ', before_year).strip()
                    parts = before_year.split()
                    if len(parts) >= 2:
                        details['brand'] = parts[0]
                        details['model'] = ' '.join(parts[1:])
                        details['year'] = year
                        print(f">> Найдено (паттерн 3): {details['brand']} {details['model']} {details['year']}")
                        break

    # Извлечение цены - несколько паттернов
    price_patterns = [
        r'(?i)Цена:\s*([\d\s,]+)',  # Цена: 123456
        r'(?i)-\s*Цена:\s*([\d\s,]+)',  # - Цена: 123456
        r'(?i)цена[:\s]+([\d\s,]+)',  # цена 123456
        r'(\d{3,})\s*₽',  # 123456₽
        r'(\d{3,})\s*руб',  # 123456 руб
        r'(\d[\d\s,]{4,})\s*(?:рублей|руб|₽|$)',  # различные варианты
    ]
    
    for pattern in price_patterns:
        price_match = re.search(pattern, text)
        if price_match:
            try:
                price_str = price_match.group(1).replace(' ', '').replace(',', '')
                details['price'] = float(price_str)
                print(f">> Найдена цена: {details['price']}")
                break
            except (ValueError, TypeError):
                continue
    
    print(f">> Итоговые данные: brand={details['brand']}, model={details['model']}, year={details['year']}, price={details['price']}")
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
    
    # Загрузка фотографий в Cloudinary
    cloudinary_urls = []
    if ann.get("photos"):
        print(f">> Загрузка {len(ann['photos'])} фото в Cloudinary...")
        for i, photo_path in enumerate(ann["photos"]):
            if os.path.exists(photo_path):
                # Создаем уникальный public_id для Cloudinary
                public_id = f"car_{custom_id}_{i+1}"
                
                # Загружаем в Cloudinary
                upload_result = upload_image_to_cloudinary(photo_path, public_id=public_id)
                if upload_result and upload_result.get('secure_url'):
                    cloudinary_url = upload_result['secure_url']
                    cloudinary_urls.append(cloudinary_url)
                    print(f">> Фото {i+1} загружено в Cloudinary: {cloudinary_url}")
                else:
                    print(f">> Ошибка загрузки фото {i+1} в Cloudinary")
        print(f">> Загружено в Cloudinary: {len(cloudinary_urls)} из {len(ann['photos'])} фото")

    # Отправка сообщения в Telegram канал (используем локальные файлы для Telegram)
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
        "photos": cloudinary_urls,  # Используем URL-ы из Cloudinary
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