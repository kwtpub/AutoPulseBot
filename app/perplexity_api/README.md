# Perplexity API Module

Изолированный модуль для работы с Perplexity AI API и форматирования объявлений об автомобилях.

## 🏗️ Архитектура модуля

```
app/perplexity_api/
├── __init__.py              # Публичное API модуля
├── perplexity_client.py     # Основной клиент Perplexity API
├── text_formatter.py       # Форматирование текста и промптов
├── legacy_wrapper.py       # Совместимость с существующим кодом
├── test_perplexity.py      # Комплексные тесты
└── README.md               # Эта документация
```

## 🚀 Быстрый старт

### Новый API (рекомендуется)

```python
from app.perplexity_api import PerplexityClient, PerplexityConfig

# Создание конфигурации
config = PerplexityConfig(
    api_key="your-perplexity-api-key",
    model="sonar-pro",
    temperature=0.2
)

# Использование клиента
async with PerplexityClient(config) as client:
    result = await client.process_text("Опиши Toyota Camry 2015")
    print(result)
```

### Legacy API (совместимость)

```python
from app.perplexity_api.legacy_wrapper import PerplexityProcessor

# Работает точно так же как старый код
processor = PerplexityProcessor("your-api-key")
prompt = processor.create_prompt(
    announcement_text="Toyota Camry 2015",
    ocr_data="дополнительные данные",
    custom_id="123",
    markup_percentage=15.0
)
result = await processor.process_text(prompt)
```

## 📋 Основные компоненты

### 1. PerplexityClient

Современный асинхронный клиент с расширенными возможностями:

- ✅ Retry логика с экспоненциальным backoff
- ✅ Различные типы ошибок (Auth, RateLimit, Server, Network)
- ✅ Context manager поддержка
- ✅ Гибкая конфигурация
- ✅ Тестирование соединения

```python
from app.perplexity_api import PerplexityClient, PerplexityConfig

config = PerplexityConfig(
    api_key="your-key",
    model="sonar-pro",
    temperature=0.2,
    max_tokens=1000,
    timeout=60,
    max_retries=3,
    retry_delay=1.0
)

async with PerplexityClient(config) as client:
    # Простой запрос
    result = await client.process_text("Ваш промпт")
    
    # Расширенный запрос
    messages = [
        {"role": "system", "content": "Ты эксперт по автомобилям"},
        {"role": "user", "content": "Опиши BMW X5"}
    ]
    response = await client.chat_completion(messages)
    
    # Тест соединения
    is_connected = await client.test_connection()
```

### 2. Text Formatter

Специализированные функции для работы с автомобильными объявлениями:

```python
from app.perplexity_api.text_formatter import (
    extract_car_info_from_text,
    create_car_description_prompt,
    format_car_announcement,
    validate_car_announcement_format
)

# Извлечение информации об авто
text = "Продам Toyota Camry 2015, цена 1500000 руб, пробег 120000 км"
car_info = extract_car_info_from_text(text)
print(f"Год: {car_info.year}, Цена: {car_info.price}")

# Создание промпта
prompt = create_car_description_prompt(
    announcement_text=text,
    ocr_data="дополнительная информация",
    custom_id="123",
    markup_percentage=15.0
)

# Форматирование финального объявления
announcement = format_car_announcement(
    brand="Toyota",
    model="Camry", 
    year=2015,
    price=1725000,  # с наценкой 15%
    description="Отличное состояние",
    characteristics={
        "year": "2015",
        "engine": "2.0л",
        "mileage": "120000 км"
    }
)

# Валидация формата
is_valid, message = validate_car_announcement_format(announcement)
```

### 3. Legacy Wrapper

Полная совместимость с существующим кодом:

```python
from app.perplexity_api.legacy_wrapper import PerplexityProcessor

# Точно такой же интерфейс как у старого PerplexityProcessor
processor = PerplexityProcessor("api-key")

# Все методы работают как раньше
prompt = processor.create_prompt(text, ocr_data, custom_id, markup)
result = await processor.process_text(prompt)

# Не забывайте закрывать соединения
await processor.close()
```

## 🔧 Конфигурация

### PerplexityConfig

```python
@dataclass
class PerplexityConfig:
    api_key: str                    # Обязательно
    model: str = 'sonar-pro'       # Модель Perplexity
    base_url: str = 'https://api.perplexity.ai'
    temperature: float = 0.2        # Температура (0.0-1.0)
    max_tokens: int = 1000         # Максимум токенов
    timeout: int = 60              # Таймаут запроса (сек)
    max_retries: int = 3           # Количество повторов
    retry_delay: float = 1.0       # Задержка между повторами
```

### Поддерживаемые модели

- `sonar-pro` (рекомендуется) - доступ к интернету
- `sonar` - базовая модель
- `llama-3.1-sonar-small-128k-online`
- `llama-3.1-sonar-large-128k-online`

## 🎯 Примеры использования

### Полный цикл обработки объявления

```python
import asyncio
from app.perplexity_api import PerplexityClient, PerplexityConfig
from app.perplexity_api.text_formatter import create_car_description_prompt

async def process_car_announcement():
    # Исходные данные
    announcement_text = "Продам BMW X5 2018, состояние отличное"
    ocr_data = "На фото видно: пробег 85000 км, двигатель 2.0л"
    markup_percentage = 15.0
    
    # Конфигурация
    config = PerplexityConfig(
        api_key="your-perplexity-api-key",
        model="sonar-pro",
        temperature=0.2
    )
    
    # Обработка
    async with PerplexityClient(config) as client:
        # Создание промпта
        prompt = create_car_description_prompt(
            announcement_text=announcement_text,
            ocr_data=ocr_data,
            custom_id="auto_123",
            markup_percentage=markup_percentage
        )
        
        # Получение результата
        formatted_announcement = await client.process_text(prompt)
        print("Готовое объявление:")
        print(formatted_announcement)

# Запуск
asyncio.run(process_car_announcement())
```

### Batch обработка

```python
async def process_multiple_announcements(announcements):
    config = PerplexityConfig(api_key="your-key")
    
    async with PerplexityClient(config) as client:
        tasks = []
        
        for ann in announcements:
            prompt = create_car_description_prompt(
                ann["text"], ann["ocr"], ann["id"], 15.0
            )
            task = client.process_text(prompt)
            tasks.append(task)
        
        # Параллельная обработка
        results = await asyncio.gather(*tasks)
        return results
```

## ⚠️ Обработка ошибок

Модуль предоставляет специализированные исключения:

```python
from app.perplexity_api.perplexity_client import (
    PerplexityError,
    PerplexityAPIError,
    PerplexityAuthError,
    PerplexityRateLimitError,
    PerplexityServerError,
    PerplexityNetworkError
)

try:
    async with PerplexityClient(config) as client:
        result = await client.process_text("промпт")
        
except PerplexityAuthError:
    print("Неверный API ключ")
except PerplexityRateLimitError:
    print("Превышен лимит запросов")
except PerplexityServerError:
    print("Ошибка сервера Perplexity")
except PerplexityNetworkError:
    print("Проблемы с сетью")
except PerplexityAPIError as e:
    print(f"Общая ошибка API: {e}")
```

## 🧪 Тестирование

### Запуск тестов

```bash
# Все тесты (без интеграционных)
python -m pytest app/perplexity_api/test_perplexity.py -v

# Только unit тесты
python -m pytest app/perplexity_api/test_perplexity.py -v -m "not integration"

# Интеграционные тесты (требуют API ключ)
PERPLEXITY_API_KEY=your-key python -m pytest app/perplexity_api/test_perplexity.py -v -m integration
```

### Тест подключения

```python
from app.perplexity_api.legacy_wrapper import test_perplexity_connection

# Быстрая проверка API ключа
is_working = test_perplexity_connection("your-api-key")
print(f"API работает: {is_working}")
```

## 🔄 Миграция с старого кода

### Автоматическая миграция

Существующий код **продолжит работать без изменений**:

```python
# Старый код (продолжает работать)
from app.core.perplexity import PerplexityProcessor
```

Просто замените импорт на:

```python
# Новый код (с улучшениями)
from app.perplexity_api.legacy_wrapper import PerplexityProcessor
```

### Поэтапная миграция

1. **Этап 1**: Замените импорты на legacy wrapper
2. **Этап 2**: Постепенно переходите на новый API
3. **Этап 3**: Используйте расширенные возможности

## 📊 Производительность

### Сравнение с legacy кодом

| Функция | Legacy | Новый модуль |
|---------|--------|--------------|
| Retry логика | ❌ | ✅ 3 попытки |
| Обработка ошибок | Базовая | ✅ Детализированная |
| Timeout контроль | ❌ | ✅ Настраиваемый |
| Context manager | ❌ | ✅ Автоматическое закрытие |
| Тестирование | Ограниченное | ✅ Полное покрытие |
| Типизация | ❌ | ✅ Type hints |

### Рекомендации по использованию

- ✅ Используйте **context manager** для автоматического управления ресурсами
- ✅ Настройте **retry_delay** под вашу нагрузку
- ✅ Используйте **test_connection()** для проверки API ключа
- ✅ Обрабатывайте специфические исключения вместо общих
- ✅ Кэшируйте клиента при множественных запросах

## 🔗 Связанные модули

- `app/ocr_api/` - Модуль OCR для извлечения текста из изображений
- `app/storage_api/` - Модуль для работы с базой данных
- `app/utils/announcement_processor.py` - Основной процессор объявлений

## 📝 История изменений

### v1.0.0
- ✅ Создание изолированного модуля
- ✅ Современный асинхронный клиент  
- ✅ Специализированное форматирование автомобильных объявлений
- ✅ Legacy wrapper для совместимости
- ✅ Комплексные тесты
- ✅ Детальная документация 