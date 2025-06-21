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
from app.bot.database import SessionLocal, Car

def extract_car_details(text: str):
    """Извлекает детали автомобиля из текста с помощью регулярных выражений."""
    details = {
        'brand': None,
        'model': None,
        'year': None,
        'price': None
    }
    title_match = re.search(r'^(.*?)\s*\[(\d{4})\]', text)
    if title_match:
        full_model_name = title_match.group(1).strip()
        brand_model_parts = full_model_name.split(' ', 1)
        details['brand'] = brand_model_parts[0]
        details['model'] = brand_model_parts[1] if len(brand_model_parts) > 1 else None
        details['year'] = int(title_match.group(2))

    price_match = re.search(r'(?i)Цена:\s*([\d\s,]+)', text)
    if price_match:
        try:
            price_str = price_match.group(1).replace(' ', '').replace(',', '')
            details['price'] = float(price_str)
        except (ValueError, TypeError):
            details['price'] = None
    return details

async def process_all_cars_from_channel():
    print(">>> Запуск конвейера обработки автомобилей...")
    load_dotenv()
    source_channel = os.getenv("TELEGRAM_CHANNEL")
    if not source_channel:
        print("TELEGRAM_CHANNEL не задан в .env")
        return

    # Получаем параметры из config.ini
    limit, start_from_id = get_telegram_config()
    markup_percentage = get_pricing_config()
    
    print(f">>> Получение объявлений из канала {source_channel} (лимит: {limit}, старт с ID: {start_from_id or 'последние'})...")
    announcements = await fetch_announcements_from_channel(source_channel, limit=limit, start_from_id=start_from_id)
    print(f">>> Получено {len(announcements)} объявлений.")
    
    api_key = os.getenv("PERPLEXITY_API_KEY")
    if not api_key:
        print("PERPLEXITY_API_KEY не найден в .env")
        return
    perplexity = PerplexityProcessor(api_key)
    formatter = MessageFormatter()

    db = SessionLocal()

    try:
        for idx, ann in enumerate(announcements, 1):
            print(f"\n--- Обработка объявления {idx}/{len(announcements)} ---")
            text = ann["text"]
            photos = ann["photos"]
            temp_dir = ann["temp_dir"]
            message_id = ann["id"]

            # Ограничиваем количество фото максимум 8
            photos = photos[:8]

            # OCR для всех фото, объединяем результаты
            ocr_texts = []
            if photos:
                print(f">> Запуск OCR для {len(photos)} фото...")
            for photo_path in photos:
                ocr = OCRProcessor(lang='ru', use_yandex=True)
                ocr_text = ocr.extract_text(photo_path)
                print(f"OCR результат для {photo_path}:", ocr_text)
                if not ocr_text.strip() or ocr_text.startswith('Ошибка разбора ответа'):
                    continue
                ocr_texts.append(ocr_text)
            ocr_data = '\n'.join(ocr_texts)
            if ocr_data:
                print(">> OCR завершен. Результат получен.")

            # Попытка извлечь основные данные для заголовка и цены
            full_text_for_parsing = f"{text}\n{ocr_data}"
            
            brand_model_match = re.search(r'(?i)(?:Марка и модель|Продаётся|автомобиль)\s*([A-Z-a-z\s]+)', full_text_for_parsing)
            year_match = re.search(r'(?i)Год выпуска:?\s*(\d{4})', full_text_for_parsing)
            price_match = re.search(r'(?i)(?:Цена|Стоимость):?\s*([\d\s,]+)', full_text_for_parsing)
            
            title_model = brand_model_match.group(1).strip() if brand_model_match else ""
            title_year = year_match.group(1).strip() if year_match else ""
            price_instruction = ""

            if price_match:
                try:
                    original_price_str = price_match.group(1).replace(' ', '').replace(',', '')
                    original_price = float(original_price_str)
                    final_price = original_price * (1 + markup_percentage / 100)
                    final_price_str = f"{int(final_price):,}".replace(",", " ")
                    price_instruction = f"- Итоговая цена (уже с наценкой): {final_price_str}"
                except (ValueError, TypeError):
                    print(f"Не удалось распознать цену: {price_match.group(1)}")
                    price_instruction = "- Цена: Не найдена в тексте. Твоя задача — найти актуальную рыночную цену для этого автомобиля в интернете."
            else:
                 price_instruction = "- Цена: Не найдена в тексте. Твоя задача — найти актуальную рыночную цену для этого автомобиля в интернете."

            # Формируем промпт для Perplexity
            prompt = f"""
Ты — эксперт по созданию продающих текстов для Telegram-каналов с продажей автомобилей.

Твоя задача — на основе предоставленных данных об автомобиле создать красивое, удобное и адаптированное под поисковые запросы объявление.

Вот данные для заголовка и цены, используй их:
- Модель: {title_model}
- Год: {title_year}
{price_instruction}

Структура объявления должна быть такой:
1. Заголовок: [Модель] [Год]
2. Цена: [Цена]
3. Краткое описание автомобиля (стильный, надёжный, экономичный и т.д.)
4. Основные характеристики (год выпуска, двигатель, мощность, пробег, кузов, привод, VIN)
5. Комплектация и опции (перечислить доступные)
6. Преимущества (уникальные плюсы автомобиля)
7. Заключительный слоган
8. Хештеги с маркой, моделью, типом кузова и коробки передач
9. Уникальный ID объявления в самом конце: ID: {message_id}

Правила:
- ID объявления является ОБЯЗАТЕЛЬНЫМ пунктом.
- Цена является ОБЯЗАТЕЛЬНЫМ пунктом. Если цена не указана выше, найди актуальную рыночную цену в интернете и укажи ее.
- Если данных для какого-то другого пункта нет, найди их в интернете. Если найти нельзя — пропусти пункт.
- Не добавляй пустые или неполные пункты.
- Не создавай призывов к действию, не приглашай на просмотр и не упоминай контакты.
- Используй простой и понятный язык.

---

ДАННЫЕ ДЛЯ АНАЛИЗА:

Данные с фото (OCR):
{ocr_data}

Текст изначального объявления:
{text}
"""
            # Отправляем в Perplexity и сразу публикуем ответ
            print(">> Отправка запроса в Perplexity API...")
            msg = await perplexity.process_text(prompt)
            print(">> Ответ от Perplexity получен.")
            print(f"\n--- Сообщение для объявления {idx} ---\n{msg}\n")

            # Удаляем нежелательные фразы
            phrases_to_remove = [
                r'(?i)приглашаем[^\n.!?]*на просмотр[^\n.!?]*',
                r'(?i)звоните[^\n.!?]*',
                r'(?i)пишите[^\n.!?]*',
                r'(?i)для уточнения деталей[^\n.!?]*',
                r'(?i)контакты[^\n.!?]*',
                r'(?i)свяжитесь[^\n.!?]*для подробностей[^\n.!?]*',
                r'(?i)записи на тест-драйв[^\n.!?]*',
                r'(?i)посмотреть автомобиль[^\n.!?]*'
            ]
            for phrase in phrases_to_remove:
                msg = re.sub(phrase, '', msg)

            msg = re.sub(r'\n\n+', '\n\n', msg).strip()  # чистим лишние пустые строки и пробелы

            # --- ГЕНЕРАЦИЯ УНИКАЛЬНОГО ID ---
            custom_id = str(random.randint(10000000, 99999999))
            # Убедимся, что ID действительно уникален
            while db.query(Car).filter(Car.custom_id == custom_id).first():
                custom_id = str(random.randint(10000000, 99999999))
            print(f">> Сгенерирован уникальный ID для поста: {custom_id}")
            # --- КОНЕЦ ГЕНЕРАЦИИ ---

            # --- ПРЕДВАРИТЕЛЬНОЕ СОХРАНЕНИЕ В БД ---
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
                status='pending_publication' # Временный статус
            )
            db.add(new_car)
            db.commit()
            db.refresh(new_car)
            print(f">> Автомобиль предварительно сохранен в базу с ID {new_car.id}.")
            # --- КОНЕЦ ПРЕДВАРИТЕЛЬНОГО СОХРАНЕНИЯ ---

            # --- ПУБЛИКАЦИЯ И ОБНОВЛЕНИЕ В БД ---
            print(">> Отправка сообщения в Telegram...")
            target_msg_id, photo_ids = await send_message_with_photos_to_channel(msg, photos)
            
            if target_msg_id:
                # Обновляем запись в базе, добавляя ID из Telegram
                new_car.target_channel_message_id = target_msg_id
                new_car.photos = photo_ids # Сохраняем file_id
                new_car.status = 'available'
                db.commit()
                print(f">> Пост опубликован. Запись в БД обновлена (ID поста: {target_msg_id}).")
            else:
                # Если публикация не удалась, удаляем запись из БД
                print(">> Публикация не удалась. Откат записи в БД.")
                db.delete(new_car)
                db.commit()
            # --- КОНЕЦ ПУБЛИКАЦИИ И ОБНОВЛЕНИЯ ---

    finally:
        db.close()
        # После отправки всех сообщений — удалить temp
        temp_dir = 'temp'
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        # Временная папка 'downloads' создается в channel_parser.py
        downloads_dir = 'downloads'
        if os.path.exists(downloads_dir):
            shutil.rmtree(downloads_dir)
            print(">>> Временная папка 'downloads' удалена.")
        print(">>> Конвейер завершил работу.")

if __name__ == "__main__":
    asyncio.run(process_all_cars_from_channel()) 