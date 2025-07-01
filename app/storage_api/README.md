# Storage API Module

Изолированный модуль для работы с базой данных автомобилей через HTTP API.

## ⚠️ ВАЖНО: ЭТОТ МОДУЛЬ НЕ ТРОГАЕМ!

Этот модуль создан для изоляции логики работы с базой данных от основного кода бота. 
**НЕ ИЗМЕНЯЙТЕ КОД В ЭТОЙ ПАПКЕ** без крайней необходимости.

## Структура модуля

```
app/storage_api/
├── __init__.py              # Инициализация модуля
├── database_client.py       # Основной HTTP клиент для работы с API
├── legacy_wrapper.py        # Обертки для совместимости с старым кодом
├── test_storage.py         # Тестовый скрипт
└── README.md               # Эта документация
```

## Основные компоненты

### 1. DatabaseClient (database_client.py)

Основной HTTP клиент для работы с Node.js API базы данных:

- `health_check()` - проверка работы API
- `save_car(car_data)` - сохранение автомобиля
- `check_duplicate(message_id, channel)` - проверка дубликатов
- `get_car(custom_id)` - получение автомобиля по ID
- `get_all_cars(limit, offset)` - получение списка автомобилей

### 2. Legacy Wrapper (legacy_wrapper.py)

Обертки для совместимости с существующим кодом:

- `send_car_to_node(car_dict)` - замена старой функции отправки
- `check_duplicate_car(msg_id, channel)` - замена старой функции проверки
- `test_database_connection()` - тест подключения

### 3. CarData (database_client.py)

Структура данных для автомобиля:

```python
@dataclass
class CarData:
    custom_id: str
    source_message_id: int
    source_channel_name: str
    brand: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    price: Optional[float] = None
    description: Optional[str] = None
    photos: Optional[List[str]] = None
    status: str = 'available'
    target_channel_message_id: Optional[int] = None
```

## Использование

### Простой способ (рекомендуется)

```python
from app.storage_api.legacy_wrapper import send_car_to_node, check_duplicate_car

# Сохранение автомобиля
car_data = {
    'custom_id': '12345678',
    'source_message_id': 1001,
    'source_channel_name': '@source_channel',
    'brand': 'Toyota',
    'model': 'Camry',
    'year': 2020,
    'price': 1500000.0,
    'description': 'Отличное состояние',
    'photos': ['https://cloudinary.com/image1.jpg'],
    'status': 'available'
}

result = send_car_to_node(car_data)
print(result)  # {'message': 'Car saved successfully'}

# Проверка дубликата
duplicate = check_duplicate_car(1001, '@source_channel')
if duplicate:
    print(f"Найден дубликат: {duplicate['custom_id']}")
```

### Продвинутый способ

```python
from app.storage_api.database_client import get_client, CarData

client = get_client()

# Проверка работы API
if client.health_check():
    print("API работает")

# Создание объекта автомобиля
car = CarData(
    custom_id='12345678',
    source_message_id=1001,
    source_channel_name='@source_channel',
    brand='Toyota',
    model='Camry'
)

# Сохранение
result = client.save_car(car)
```

## Тестирование

Запуск тестов:

```bash
cd app/storage_api
python test_storage.py
```

Тесты проверяют:
- ✅ Подключение к API
- ✅ Health check
- ✅ Проверку дубликатов
- ✅ Сохранение автомобилей
- ✅ Получение данных

## Настройки

Модуль использует следующие настройки:

- **API URL**: `http://localhost:3001` (по умолчанию)
- **Таймауты**: 5-10 секунд в зависимости от операции
- **Повторные попытки**: Автоматическая обработка ошибок

## Логирование

Модуль ведет подробное логирование всех операций:

```
💾 Сохранение автомобиля: 12345678
✅ Автомобиль сохранен: 12345678
🔍 Найден дубликат: 87654321
⚠️ Ошибка проверки дубликата: 500
```

## Обработка ошибок

Модуль gracefully обрабатывает все типы ошибок:

- **Сетевые ошибки**: Возврат `None` или `False`
- **Таймауты**: Логирование и безопасный возврат
- **Ошибки API**: Детальное логирование ответов сервера

## Требования

- `requests` - для HTTP запросов
- `python-dotenv` - для переменных окружения (опционально)

Node.js API должен быть запущен на `localhost:3001` с эндпоинтами:

- `GET /api/health` - проверка здоровья
- `POST /api/cars` - сохранение автомобиля
- `GET /api/cars/check-duplicate/{msg_id}/{channel}` - проверка дубликата
- `GET /api/cars/{custom_id}` - получение автомобиля
- `GET /api/cars` - получение списка автомобилей

## Новый Data Formatter (data_formatter.py)

Модуль автоматического форматирования данных:

### `extract_car_details(text)`
Извлекает структурированные данные из текста объявления с помощью регулярных выражений.

### `format_car_data_for_storage(...)` 
Автоматически форматирует и структурирует данные для сохранения в базе.

### `save_car_with_formatting(...)` ⭐ НОВАЯ ФУНКЦИЯ

```python
from app.storage_api.legacy_wrapper import save_car_with_formatting

# Автоматическое форматирование + сохранение
result = save_car_with_formatting(
    custom_id='12345678',
    source_message_id=1001,
    source_channel_name='@channel',
    description='Toyota Camry [2020] цена 1500000₽',
    cloudinary_urls=['https://cloudinary.com/1.jpg'],
    target_msg_id=2001
)

# Автоматически извлечет: brand='Toyota', model='Camry', year=2020, price=1500000.0
```

## Миграция

Для перехода на новый модуль замените импорты:

```python
# Старый код
from app.utils.send_to_node import send_car_to_node
from app.utils.channel_parser import check_duplicate_car

# Новый код  
from app.storage_api.legacy_wrapper import send_car_to_node, check_duplicate_car

# Еще лучше - используйте новую функцию с автоформатированием:
from app.storage_api.legacy_wrapper import save_car_with_formatting
```

Функции работают абсолютно так же, как раньше! 