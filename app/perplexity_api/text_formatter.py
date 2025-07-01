"""
Text Formatter - форматирование текста и создание промптов для объявлений об автомобилях
Специализированные функции для создания привлекательных описаний автомобилей
"""

import re
from typing import Dict, Optional, Tuple, List
from dataclasses import dataclass
from datetime import datetime

@dataclass
class CarInfo:
    """Структура данных об автомобиле"""
    brand: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    price: Optional[float] = None
    mileage: Optional[int] = None
    engine_volume: Optional[str] = None
    transmission: Optional[str] = None
    drive_type: Optional[str] = None
    body_type: Optional[str] = None
    color: Optional[str] = None
    fuel_type: Optional[str] = None

def extract_car_info_from_text(text: str) -> CarInfo:
    """
    Извлекает информацию об автомобиле из текста объявления
    
    Args:
        text: Текст объявления
        
    Returns:
        CarInfo с извлеченными данными
    """
    car_info = CarInfo()
    text_lower = text.lower()
    
    # Извлечение года (4 цифры от 1980 до текущего года + 2)
    current_year = datetime.now().year
    year_pattern = r'\b(19[8-9]\d|20[0-2]\d)\b'
    year_match = re.search(year_pattern, text)
    if year_match:
        year = int(year_match.group(1))
        if 1980 <= year <= current_year + 2:
            car_info.year = year
    
    # Извлечение цены (различные форматы)
    price_patterns = [
        r'(\d{1,3}(?:\s?\d{3})*)\s*(?:тысяч|тыс|т\.р\.?|руб)',
        r'(\d{1,3}(?:\s?\d{3})*)\s*₽',
        r'цена[:\s]*(\d{1,3}(?:\s?\d{3})*)',
        r'(\d{1,3}(?:\s?\d{3})*)\s*000'
    ]
    
    for pattern in price_patterns:
        price_match = re.search(pattern, text_lower)
        if price_match:
            price_str = price_match.group(1).replace(' ', '')
            try:
                price = float(price_str)
                # Конвертация в рубли если нужно
                if price < 10000:  # Вероятно в тысячах
                    price *= 1000
                car_info.price = price
                break
            except ValueError:
                continue
    
    # Извлечение пробега
    mileage_patterns = [
        r'(\d{1,3}(?:\s?\d{3})*)\s*(?:км|тыс\.?\s*км)',
        r'пробег[:\s]*(\d{1,3}(?:\s?\d{3})*)',
    ]
    
    for pattern in mileage_patterns:
        mileage_match = re.search(pattern, text_lower)
        if mileage_match:
            mileage_str = mileage_match.group(1).replace(' ', '')
            try:
                mileage = int(mileage_str)
                # Если пробег в тысячах
                if mileage < 1000:
                    mileage *= 1000
                car_info.mileage = mileage
                break
            except ValueError:
                continue
    
    # Извлечение объема двигателя
    engine_pattern = r'(\d+\.?\d*)\s*(?:л\.?|литр)'
    engine_match = re.search(engine_pattern, text_lower)
    if engine_match:
        car_info.engine_volume = engine_match.group(1)
    
    # Определение коробки передач
    if any(word in text_lower for word in ['автомат', 'акпп', 'автоматическая']):
        car_info.transmission = 'Автомат'
    elif any(word in text_lower for word in ['механика', 'мкпп', 'механическая']):
        car_info.transmission = 'Механика'
    
    # Определение типа привода
    if any(word in text_lower for word in ['полный привод', '4wd', 'awd']):
        car_info.drive_type = 'Полный'
    elif any(word in text_lower for word in ['передний привод', 'fwd']):
        car_info.drive_type = 'Передний'
    elif any(word in text_lower for word in ['задний привод', 'rwd']):
        car_info.drive_type = 'Задний'
    
    return car_info

def create_car_description_prompt(
    announcement_text: str,
    ocr_data: str,
    custom_id: str,
    markup_percentage: float,
    car_info: Optional[CarInfo] = None
) -> str:
    """
    Создает оптимизированный промпт для Perplexity на основе данных объявления
    
    Args:
        announcement_text: Исходный текст объявления
        ocr_data: Данные OCR из изображений
        custom_id: Кастомный ID объявления
        markup_percentage: Процент наценки
        car_info: Предварительно извлеченная информация об автомобиле
        
    Returns:
        Готовый промпт для Perplexity
    """
    
    if not car_info:
        car_info = extract_car_info_from_text(announcement_text)
    
    # Создание контекстуального промпта
    prompt = f"""
Ты — эксперт по автомобилям и профессиональный копирайтер. Создай привлекательное объявление для продажи автомобиля.

ИСХОДНЫЕ ДАННЫЕ:
Текст объявления: {announcement_text}

Дополнительная информация из фото (OCR): {ocr_data if ocr_data else "Информация из фото отсутствует"}

КРИТИЧЕСКИ ВАЖНО - ФОРМАТ ПЕРВОЙ СТРОКИ:
[Марка] [Модель] [Год] - Цена: [цена с наценкой {markup_percentage}%]

ТРЕБОВАНИЯ К РЕЗУЛЬТАТУ:
1. ОБЯЗАТЕЛЬНО начни с формата: [Марка] [Модель] [Год] - Цена: [цена]
2. Добавь наценку {markup_percentage}% к исходной цене
3. Создай краткое структурированное описание (максимум 800 символов)
4. Включи основные характеристики в читаемом формате
5. Используй привлекательные формулировки для покупателей
6. Добавь релевантные хэштеги

СТРУКТУРА ОТВЕТА:
[Марка] [Модель] [Год] - Цена: [цена с наценкой]

💫 Краткое привлекательное описание автомобиля (2-3 предложения)

📋 Основные характеристики:
• Год: [год] | Двигатель: [объем] л | Пробег: [пробег] км
• Коробка: [тип] | Привод: [тип] | Кузов: [тип]

🚗 [Марка] [Модель] — [короткий продающий слоган]

#марка#модель #год #автомобиль #продажа

ОБЯЗАТЕЛЬНО: Первая строка должна точно соответствовать формату [Марка] [Модель] [Год]!
    """
    
    return prompt.strip()

def format_car_announcement(
    brand: str,
    model: str,
    year: int,
    price: float,
    description: str,
    characteristics: Dict[str, str],
    hashtags: List[str] = None
) -> str:
    """
    Форматирует финальное объявление об автомобиле
    
    Args:
        brand: Марка автомобиля
        model: Модель автомобиля  
        year: Год выпуска
        price: Цена
        description: Описание
        characteristics: Словарь характеристик
        hashtags: Список хэштегов
        
    Returns:
        Отформатированное объявление
    """
    
    # Форматирование цены
    price_formatted = f"{int(price):,}".replace(',', ' ')
    
    # Заголовок
    header = f"[{brand}] [{model}] [{year}] - Цена: {price_formatted} ₽"
    
    # Описание
    desc_section = f"💫 {description}"
    
    # Характеристики
    char_lines = []
    if characteristics:
        char_lines.append("📋 Основные характеристики:")
        
        # Группируем характеристики по строкам
        main_chars = []
        if 'year' in characteristics:
            main_chars.append(f"Год: {characteristics['year']}")
        if 'engine' in characteristics:
            main_chars.append(f"Двигатель: {characteristics['engine']}")
        if 'mileage' in characteristics:
            main_chars.append(f"Пробег: {characteristics['mileage']}")
        
        if main_chars:
            char_lines.append("• " + " | ".join(main_chars))
        
        # Вторая строка характеристик
        second_chars = []
        if 'transmission' in characteristics:
            second_chars.append(f"Коробка: {characteristics['transmission']}")
        if 'drive' in characteristics:
            second_chars.append(f"Привод: {characteristics['drive']}")
        if 'body' in characteristics:
            second_chars.append(f"Кузов: {characteristics['body']}")
            
        if second_chars:
            char_lines.append("• " + " | ".join(second_chars))
    
    # Слоган
    slogan = f"🚗 {brand} {model} — надежность и качество!"
    
    # Хэштеги
    if not hashtags:
        hashtags = [
            f"#{brand.lower()}", 
            f"#{model.lower().replace(' ', '')}", 
            f"#{year}",
            "#автомобиль", 
            "#продажа"
        ]
    
    hashtag_line = " ".join(hashtags)
    
    # Сборка финального текста
    sections = [header, "", desc_section]
    
    if char_lines:
        sections.append("")
        sections.extend(char_lines)
    
    sections.extend(["", slogan, "", hashtag_line])
    
    return "\n".join(sections)

def apply_markup_to_price(original_price: float, markup_percentage: float) -> float:
    """
    Применяет наценку к цене
    
    Args:
        original_price: Исходная цена
        markup_percentage: Процент наценки
        
    Returns:
        Цена с наценкой
    """
    return original_price * (1 + markup_percentage / 100)

def validate_car_announcement_format(text: str) -> Tuple[bool, str]:
    """
    Проверяет соответствие текста требуемому формату объявления
    
    Args:
        text: Текст для проверки
        
    Returns:
        Tuple[bool, str]: (валидность, сообщение об ошибке)
    """
    
    lines = text.strip().split('\n')
    if not lines:
        return False, "Пустой текст"
    
    first_line = lines[0].strip()
    
    # Проверка формата первой строки
    pattern = r'^\[.+\]\s*\[.+\]\s*\[\d{4}\]\s*-\s*Цена:\s*[\d\s]+.*₽?'
    
    if not re.match(pattern, first_line):
        return False, f"Первая строка не соответствует формату [Марка] [Модель] [Год] - Цена: [цена]. Получено: {first_line}"
    
    return True, "Формат корректен"

def extract_structured_data_from_announcement(text: str) -> Dict[str, str]:
    """
    Извлекает структурированные данные из отформатированного объявления
    
    Args:
        text: Отформатированный текст объявления
        
    Returns:
        Словарь с извлеченными данными
    """
    data = {}
    
    lines = text.strip().split('\n')
    if not lines:
        return data
    
    # Извлечение из первой строки
    first_line = lines[0].strip()
    header_pattern = r'^\[(.+?)\]\s*\[(.+?)\]\s*\[(\d{4})\]\s*-\s*Цена:\s*([\d\s]+)'
    
    header_match = re.match(header_pattern, first_line)
    if header_match:
        data['brand'] = header_match.group(1)
        data['model'] = header_match.group(2)
        data['year'] = header_match.group(3)
        data['price'] = header_match.group(4).replace(' ', '')
    
    # Извлечение характеристик
    for line in lines:
        if '|' in line and ('Год:' in line or 'Двигатель:' in line):
            # Парсинг строки характеристик
            parts = [part.strip() for part in line.split('|')]
            for part in parts:
                if ':' in part:
                    key_value = part.split(':', 1)
                    if len(key_value) == 2:
                        key = key_value[0].strip().replace('• ', '')
                        value = key_value[1].strip()
                        data[key.lower()] = value
    
    return data 