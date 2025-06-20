import os
import asyncio
from dotenv import load_dotenv
from app.utils.channel_parser import fetch_announcements_from_channel
from app.core.ocr import OCRProcessor
from app.core.perplexity import PerplexityProcessor
from app.utils.message_formatter import MessageFormatter
from app.core.telegram import send_message_to_channel, send_message_with_photos_to_channel
from app.utils.config import get_telegram_config
import re
import sys
import shutil

async def process_all_cars_from_channel():
    print(">>> Запуск конвейера обработки автомобилей...")
    load_dotenv()
    source_channel = os.getenv("TELEGRAM_CHANNEL")
    if not source_channel:
        print("TELEGRAM_CHANNEL не задан в .env")
        return

    # Получаем параметры из config.ini
    limit, start_from_id = get_telegram_config()

    print(f">>> Получение объявлений из канала {source_channel} (лимит: {limit}, старт с ID: {start_from_id or 'последние'})...")
    announcements = await fetch_announcements_from_channel(source_channel, limit=limit, start_from_id=start_from_id)
    print(f">>> Получено {len(announcements)} объявлений.")
    
    api_key = os.getenv("PERPLEXITY_API_KEY")
    if not api_key:
        print("PERPLEXITY_API_KEY не найден в .env")
        return
    perplexity = PerplexityProcessor(api_key)
    formatter = MessageFormatter()

    for idx, ann in enumerate(announcements, 1):
        print(f"\n--- Обработка объявления {idx}/{len(announcements)} ---")
        text = ann["text"]
        photos = ann["photos"]
        temp_dir = ann["temp_dir"]

        # Ограничиваем количество фото максимум 9
        photos = photos[:9]

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

        # Формируем промпт для Perplexity
        prompt = f"""
Ты — эксперт по созданию продающих текстов для Telegram-каналов с продажей автомобилей.

Твоя задача — на основе предоставленных данных об автомобиле создать красивое, удобное и адаптированное под поисковые запросы объявление с такой структурой:

1. Заголовок: [Модель] [Год]
2. Краткое описание автомобиля (стильный, надёжный, экономичный и т.д.)
3. Основные характеристики (год выпуска, двигатель, мощность, пробег, кузов, привод, VIN, масса, цвет салона, количество мест)
4. Комплектация и опции (перечислить доступные)
5. Преимущества (уникальные плюсы автомобиля)
6. Заключительный слоган
7. Хештеги с маркой, моделью, типом кузова и коробки передач

Если каких-то данных нет, сделай следующее:
- Если данные можно легко найти в интернете по марке и модели (например, тип кузова, мощность двигателя, комплектация), найди и добавь их.
- Если данные найти нельзя, просто пропусти этот пункт, чтобы текст оставался логичным и читабельным.
- Не добавляй пустые или неполные пункты.
- Не создавай призывов к действию, не приглашай на просмотр и не упоминай контакты.

Используй простой и понятный язык, избегай сложных терминов без объяснений, делай текст привлекательным и продающим.

---

Данные с фото:
{ocr_data}

Текст:
{text}
"""
        # Отправляем в Perplexity и сразу публикуем ответ
        print(">> Отправка запроса в Perplexity API...")
        result = await perplexity.process_text(prompt)
        print(">> Ответ от Perplexity получен.")
        # Если Perplexity вернул dict с main_text — используем main_text, иначе весь ответ
        if isinstance(result, dict) and 'main_text' in result:
            msg = result['main_text']
        elif isinstance(result, dict):
            msg = next(iter(result.values()))
        else:
            msg = str(result)
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

        print(">> Отправка сообщения в Telegram...")
        await send_message_with_photos_to_channel(msg, photos)
        print(f">> Сообщение для объявления {idx} успешно отправлено.")

    # После отправки всех сообщений — удалить temp
    temp_dir = 'temp'
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    print(">>> Конвейер завершил работу.")

if __name__ == "__main__":
    asyncio.run(process_all_cars_from_channel()) 