import os
import asyncio
from dotenv import load_dotenv
from app.utils.channel_parser import fetch_announcements_from_channel
from app.ocr_api.legacy_wrapper import OCRProcessor
from app.perplexity_api.legacy_wrapper import PerplexityProcessor
from app.cloudinary_api.legacy_wrapper import upload_image_to_cloudinary, get_image_url_from_cloudinary
from app.utils.message_formatter import MessageFormatter
from app.core.telegram import send_message_to_channel, send_message_with_photos_to_channel
from app.utils.config import get_telegram_config, get_pricing_config
from app.utils.id_generator import generate_custom_id, format_id_for_display
import sys
import shutil
import random
from app.storage_api.legacy_wrapper import save_car_with_formatting



async def process_single_announcement(ann, perplexity_processor, source_channel, markup_percentage):
    """
    Обрабатывает одно объявление: OCR, Perplexity, отправка в Node.js API и публикация.
    """
    message_id = ann["id"]
    print("--- Обработка объявления ID: " + str(message_id))

    # Генерация уникального custom_id в новом формате XXX-XXX
    custom_id = generate_custom_id()
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
    
    # Извлекаем данные автомобиля из OCR и текста объявления
    from app.perplexity_api.text_formatter import extract_car_info_from_text
    
    # Объединяем все доступные текстовые данные
    all_text = f"{ann.get('text', '')}\n{ocr_data}".strip()
    
    # Извлекаем структурированную информацию
    car_info = extract_car_info_from_text(all_text)
    
    # Подготавливаем данные автомобиля для нового формата
    car_data = {
        'brand': car_info.brand if car_info.brand else 'Не указана',
        'model': car_info.model if car_info.model else 'Не указана',
        'year': str(car_info.year) if car_info.year else '2023',
        'mileage': str(car_info.mileage) if car_info.mileage else '50000',
        'price': str(int(car_info.price)) if car_info.price else '2500000',
        'engine': car_info.engine_volume + 'л, бензин' if car_info.engine_volume else '2.0л, бензин',
        'transmission': car_info.transmission if car_info.transmission else 'автомат',
        'drive_type': car_info.drive_type if car_info.drive_type else 'передний',
        'trim': car_info.trim if car_info.trim else 'комфорт',
        'color': car_info.color if car_info.color else 'не указан',
        'condition': car_info.condition if car_info.condition else 'хорошее',
        'custom_id': custom_id,
        'city': 'Москва'
    }
    
    # Используем новый шаблон для создания сообщения
    formatter = MessageFormatter()
    
    # Если нужно использовать Perplexity API, создаем промпт для онлайн-продажи
    if perplexity_processor:
        from app.perplexity_api.text_formatter import CarInfo, create_car_description_prompt
        
        # Создаем объект CarInfo на основе данных
        car_info = CarInfo(
            brand=car_data['brand'],
            model=car_data['model'],
            year=car_data['year'],
            price=car_data['price'],
            mileage=car_data['mileage'],
            engine_volume=car_data['engine'],
            transmission=car_data['transmission'],
            drive_type=car_data['drive_type'],
            color=car_data['color'],
            trim=car_data['trim'],
            condition=car_data['condition'],
            custom_id=custom_id
        )
        
        # Создаем промпт для онлайн-продажи китайских авто
        prompt = create_car_description_prompt(
            car_info, 
            custom_context=f"Дополнительная информация из объявления: {ann['text']}\nДанные OCR: {ocr_data}"
        )
        
        print(">> Отправка запроса в Perplexity API с новым промптом...")
        msg = await perplexity_processor.process_text(prompt)
        print(">> Ответ от Perplexity получен.")
    else:
        # Используем стандартный шаблон без Perplexity
        msg = formatter.format_for_telegram(car_data)
    
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

    # Сохраняем автомобиль через Storage API с автоматическим форматированием
    print(">> Сохранение автомобиля в базу данных...")
    save_result = save_car_with_formatting(
        custom_id=custom_id,
        source_message_id=message_id,
        source_channel_name=source_channel,
        description=msg,
        cloudinary_urls=cloudinary_urls,
        target_msg_id=target_msg_id
    )
    
    if save_result.get('message'):
        print(f">> ✅ Автомобиль {custom_id} сохранен в базу данных")
    else:
        print(f">> ⚠️ Ошибка сохранения автомобиля {custom_id}: {save_result}")
    

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