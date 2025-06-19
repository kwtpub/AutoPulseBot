import os
import asyncio
from dotenv import load_dotenv
from app.utils.channel_parser import fetch_announcements_from_channel
from app.core.ocr import OCRProcessor
from app.core.perplexity import PerplexityProcessor
from app.utils.message_formatter import MessageFormatter
from app.core.telegram import send_message_to_channel, send_message_with_photos_to_channel
import re
import sys
import shutil

async def process_all_cars_from_channel():
    load_dotenv()
    source_channel = os.getenv("TELEGRAM_CHANNEL")
    if not source_channel:
        print("TELEGRAM_CHANNEL не задан в .env")
        return

    # Получаем start_from_id из переменной окружения или аргумента
    start_from_id = None
    if len(sys.argv) > 1:
        try:
            start_from_id = int(sys.argv[1])
        except Exception:
            start_from_id = None
    elif os.getenv("START_FROM_ID"):
        try:
            start_from_id = int(os.getenv("START_FROM_ID"))
        except Exception:
            start_from_id = None

    announcements = await fetch_announcements_from_channel(source_channel, limit=50, start_from_id=start_from_id)
    api_key = os.getenv("PERPLEXITY_API_KEY")
    if not api_key:
        print("PERPLEXITY_API_KEY не найден в .env")
        return
    perplexity = PerplexityProcessor(api_key)
    formatter = MessageFormatter()

    for idx, ann in enumerate(announcements, 1):
        text = ann["text"]
        photos = ann["photos"]
        temp_dir = ann["temp_dir"]

        # Ограничиваем количество фото максимум 9
        photos = photos[:9]

        # OCR для всех фото, объединяем результаты
        ocr_texts = []
        for photo_path in photos:
            ocr = OCRProcessor(lang='ru', use_yandex=True)
            ocr_text = ocr.extract_text(photo_path)
            print(f"OCR результат для {photo_path}:", ocr_text)
            if not ocr_text.strip() or ocr_text.startswith('Ошибка разбора ответа'):
                continue
            ocr_texts.append(ocr_text)
        ocr_data = '\n'.join(ocr_texts)

        # Формируем промпт для Perplexity
        prompt = f"""
Ты — эксперт по созданию продающих текстов для Telegram-каналов с продажей автомобилей.

Твоя задача — на основе предоставленных данных об автомобиле создать красивое, удобное и адаптированное под поисковые запросы объявление с такой структурой:

1. Заголовок: [Марка] [Модель] [Двигатель/Объём] [Год] — Ваш идеальный выбор!
2. Краткое описание автомобиля (стильный, надёжный, экономичный и т.д.)
3. Основные характеристики (год выпуска, двигатель, мощность, пробег, кузов, привод, VIN, масса, цвет салона, количество мест)
4. Комплектация и опции (перечислить доступные)
5. Преимущества (уникальные плюсы автомобиля)
6. Призыв к действию (приглашение на просмотр, контакты)
7. Заключительный слоган
8. Хештеги с маркой, моделью, типом кузова и коробки передач

Если каких-то данных нет, сделай следующее:
- Если данные можно легко найти в интернете по марке и модели (например, тип кузова, мощность двигателя, комплектация), найди и добавь их.
- Если данные найти нельзя, просто пропусти этот пункт, чтобы текст оставался логичным и читабельным.
- Не добавляй пустые или неполные пункты.

Используй простой и понятный язык, избегай сложных терминов без объяснений, делай текст привлекательным и продающим.

---

Данные с фото:
{ocr_data}

Текст:
{text}
"""
        # Отправляем в Perplexity и сразу публикуем ответ
        result = await perplexity.process_text(prompt)
        # Если Perplexity вернул dict с main_text — используем main_text, иначе весь ответ
        if isinstance(result, dict) and 'main_text' in result:
            msg = result['main_text']
        elif isinstance(result, dict):
            msg = next(iter(result.values()))
        else:
            msg = str(result)
        print(f"\n--- Сообщение для объявления {idx} ---\n{msg}\n")

        # Удаляем нежелательные фразы про просмотр, звонки, контакты
        msg = re.sub(r'(?i)(приглашаем[^\n.!?]*на просмотр[^\n.!?]*[.!?]?)', '', msg)
        msg = re.sub(r'(?i)(звоните[^\n.!?]*[.!?]?)', '', msg)
        msg = re.sub(r'(?i)(пишите[^\n.!?]*[.!?]?)', '', msg)
        msg = re.sub(r'(?i)(для уточнения деталей[^\n.!?]*[.!?]?)', '', msg)
        msg = re.sub(r'(?i)(контакты[^\n.!?]*[.!?]?)', '', msg)
        msg = re.sub(r'\n\n+', '\n\n', msg)  # чистим лишние пустые строки

        await send_message_with_photos_to_channel(msg, photos)

    # После отправки всех сообщений — удалить temp
    temp_dir = 'temp'
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)

if __name__ == "__main__":
    asyncio.run(process_all_cars_from_channel()) 