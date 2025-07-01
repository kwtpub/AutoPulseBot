# OCR API Module

Изолированный модуль для обработки изображений и извлечения текста. Поддерживает множественные OCR движки и предоставляет единый API для работы с изображениями.

## Возможности

- **Поддержка множественных OCR движков:**
  - Tesseract OCR (локальный)
  - PaddleOCR (локальный)
  - Yandex Vision API (облачный)
  - BLIP для генерации описаний изображений

- **Обработка изображений:**
  - Предварительная обработка изображений
  - Извлечение текста из одного или нескольких изображений
  - Генерация описаний изображений
  - Пакетная обработка

- **Совместимость:**
  - Обертки для совместимости со старым кодом
  - Простой и расширенный API
  - Обработка ошибок и fallback

## Установка зависимостей

```bash
# Базовые зависимости (уже должны быть установлены)
pip install pillow opencv-python requests python-dotenv

# Опциональные зависимости
pip install pytesseract  # для Tesseract OCR
pip install paddlepaddle paddleocr  # для PaddleOCR  
pip install transformers torch  # для BLIP
```

## Конфигурация

### Переменные окружения

Добавьте в ваш `.env` файл:

```env
# Для Yandex Vision API (опционально)
YANDEX_IAM_TOKEN=your_yandex_iam_token
YANDEX_FOLDER_ID=your_yandex_folder_id
```

### Настройка OCR движков

```python
from app.ocr_api import OCRConfig

# Базовая конфигурация
config = OCRConfig(
    language='ru',           # Язык OCR
    use_tesseract=True,      # Использовать Tesseract
    use_paddle=False,        # Использовать PaddleOCR
    use_yandex=False,        # Использовать Yandex Vision
    use_blip=False,          # Использовать BLIP для описаний
    preprocess_images=True   # Предобработка изображений
)
```

## Использование

### Базовое использование (высокоуровневые функции)

```python
import asyncio
from app.ocr_api import extract_text_from_image, extract_caption_from_image

async def main():
    # Извлечение текста из изображения
    text = await extract_text_from_image(
        'path/to/image.jpg',
        language='ru',
        use_yandex=True  # Использовать Yandex Vision API
    )
    print(f"Извлеченный текст: {text}")
    
    # Генерация описания изображения
    caption = await extract_caption_from_image('path/to/image.jpg')
    print(f"Описание: {caption}")

asyncio.run(main())
```

### Продвинутое использование (OCR клиент)

```python
import asyncio
from app.ocr_api import OCRClient, OCRConfig

async def advanced_example():
    # Создание конфигурации
    config = OCRConfig(
        language='ru',
        use_yandex=True,
        use_blip=True
    )
    
    # Создание клиента
    client = OCRClient(config)
    
    # Обработка одного изображения
    text = await client.extract_text('image.jpg')
    
    # Обработка нескольких изображений
    image_paths = ['img1.jpg', 'img2.jpg', 'img3.jpg']
    results = await client.process_multiple_images(image_paths)
    
    for result in results:
        print(f"Файл: {result['image_path']}")
        print(f"Текст: {result['text']}")
        print(f"Успех: {result['success']}")
        print("-" * 40)
    
    # Проверка состояния сервисов
    status = client.health_check()
    print(f"Статус сервисов: {status}")

asyncio.run(advanced_example())
```

### Совместимость со старым кодом

```python
# Совместимость с app.core.ocr.OCRProcessor
from app.ocr_api.legacy_wrapper import OCRProcessor

async def legacy_example():
    # Старый интерфейс продолжает работать
    ocr = OCRProcessor(lang='ru', use_yandex=True)
    text = await ocr.extract_text('image.jpg')
    print(text)

# Совместимость с функциями
from app.ocr_api.legacy_wrapper import extract_text_from_image, blip_image_caption

async def legacy_functions():
    # Функция из text_reader.py
    text = await extract_text_from_image('image.jpg')
    
    # Функция BLIP (синхронная)
    caption = blip_image_caption('image.jpg')
```

### Пакетная обработка

```python
import asyncio
from app.ocr_api import process_images_ocr

async def batch_processing():
    image_paths = ['img1.jpg', 'img2.jpg', 'img3.jpg']
    
    # Получить список текстов
    texts = await process_images_ocr(
        image_paths, 
        language='ru',
        use_yandex=True
    )
    
    for i, text in enumerate(texts):
        print(f"Изображение {i+1}: {text}")

asyncio.run(batch_processing())
```

## API Reference

### OCRClient

Основной класс для работы с OCR.

#### Методы:

- `extract_text(image_path: str) -> str` - Извлечение текста из изображения
- `extract_text_tesseract(image_path: str) -> str` - Tesseract OCR
- `extract_text_paddle(image_path: str) -> str` - PaddleOCR
- `extract_text_yandex(image_path: str) -> str` - Yandex Vision API
- `generate_image_caption(image_path: str) -> str` - BLIP описание
- `process_multiple_images(image_paths: List[str]) -> List[Dict]` - Пакетная обработка
- `health_check() -> Dict` - Проверка состояния сервисов

### OCRConfig

Конфигурация для OCR клиента.

#### Параметры:

- `language: str = 'ru'` - Язык OCR
- `use_tesseract: bool = True` - Использовать Tesseract
- `use_paddle: bool = False` - Использовать PaddleOCR
- `use_yandex: bool = False` - Использовать Yandex Vision
- `use_blip: bool = False` - Использовать BLIP
- `preprocess_images: bool = True` - Предобработка изображений
- `yandex_iam_token: Optional[str] = None` - Yandex IAM токен
- `yandex_folder_id: Optional[str] = None` - Yandex Folder ID

### Высокоуровневые функции

- `extract_text_from_image(image_path, language='ru', use_yandex=True, ...)` - Извлечение текста
- `extract_text_from_images(image_paths, language='ru', use_yandex=True, ...)` - Множественные изображения
- `extract_caption_from_image(image_path)` - Описание изображения
- `extract_text_and_caption(image_path, ...)` - Текст и описание

### Legacy обертки

- `OCRProcessor` - Совместимость со старым классом
- `extract_text_from_image` - Глобальная функция для text_reader.py
- `blip_image_caption` - Синхронная BLIP функция
- `test_ocr_connection` - Проверка состояния сервисов

## Обработка ошибок

```python
import asyncio
from app.ocr_api import OCRClient, OCRConfig

async def error_handling():
    try:
        client = OCRClient(OCRConfig(use_yandex=True))
        text = await client.extract_text('nonexistent.jpg')
    except FileNotFoundError:
        print("Файл не найден")
    except ValueError as e:
        print(f"Ошибка конфигурации: {e}")
    except Exception as e:
        print(f"Общая ошибка OCR: {e}")
```

## Тестирование

Запуск тестов:

```bash
cd app/ocr_api
python test_ocr.py
```

Тесты проверяют:
- Состояние всех OCR сервисов
- Работу основного клиента
- Yandex Vision API (если настроен)
- Совместимость со старым кодом
- Высокоуровневые функции

## Производительность

### Рекомендации по выбору OCR движка:

1. **Tesseract** - хорош для четкого печатного текста, бесплатный
2. **PaddleOCR** - лучше для рукописного текста и азиатских языков
3. **Yandex Vision** - высокое качество, облачный, требует интернет

### Оптимизация:

- Используйте `preprocess_images=True` для улучшения качества OCR
- Для пакетной обработки используйте `process_multiple_images`
- Настройте ленивую инициализацию для экономии памяти
- Кэшируйте результаты для повторно используемых изображений

## Миграция со старого кода

Замените импорты в существующем коде:

```python
# Старый код
from app.ocr_api.legacy_wrapper import OCRProcessor

# Новый код (полная совместимость)
from app.ocr_api.legacy_wrapper import OCRProcessor

# Или используйте новый API
from app.ocr_api import OCRClient, OCRConfig
```

## Логирование

Модуль использует стандартное логирование Python. Для включения debug логов:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Архитектура

```
app/ocr_api/
├── __init__.py          # Публичный API модуля
├── ocr_client.py        # Основной OCR клиент
├── text_extractor.py    # Высокоуровневые функции
├── legacy_wrapper.py    # Обертки для совместимости
├── test_ocr.py         # Тестирование
└── README.md           # Документация
```

## Устранение неполадок

### Tesseract не найден
```bash
# macOS
brew install tesseract

# Ubuntu/Debian
sudo apt-get install tesseract-ocr

# Добавить языки
sudo apt-get install tesseract-ocr-rus
```

### PaddleOCR ошибки
```bash
pip install paddlepaddle
pip install paddleocr
```

### Yandex API ошибки
1. Проверьте правильность токенов в `.env`
2. Убедитесь что токен не истек
3. Проверьте квоты в Yandex Cloud

### BLIP модель
```bash
pip install transformers torch
# Модель скачается автоматически при первом использовании
``` 