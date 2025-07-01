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
    trim: Optional[str] = None
    condition: Optional[str] = None
    custom_id: Optional[str] = None

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
    
    # Извлечение марки и модели (первая строка текста, обычно содержит марку и модель)
    lines = text.strip().split('\n')
    first_line = lines[0].strip() if lines else ""
    
    # Список популярных китайских марок для распознавания
    chinese_brands = [
        'geely', 'chery', 'byd', 'haval', 'great wall', 'changan', 'dongfeng',
        'faw', 'jac', 'lifan', 'zotye', 'brilliance', 'foton', 'maxus',
        'tank', 'ora', 'li auto', 'nio', 'xpeng', 'aiways', 'lixiang'
    ]
    
    # Ищем марку в первой строке
    first_line_lower = first_line.lower()
    for brand in chinese_brands:
        if brand in first_line_lower:
            # Находим позицию марки
            brand_pos = first_line_lower.find(brand)
            # Извлекаем часть после марки как модель
            after_brand = first_line[brand_pos + len(brand):].strip()
            
            # Убираем год из модели если он есть
            year_pattern = r'\s*(19|20)\d{2}.*'
            model_without_year = re.sub(year_pattern, '', after_brand).strip()
            
            car_info.brand = brand.title()
            car_info.model = model_without_year if model_without_year else "Неизвестная модель"
            break
    
    # Если марка не найдена, попробуем извлечь из начала строки
    if not car_info.brand and first_line:
        # Ищем паттерн "Слово Слово год"
        brand_model_pattern = r'^([A-Za-zА-Яа-я]+)\s+([A-Za-zА-Яа-я0-9\s]+?)\s+(\d{4})'
        match = re.search(brand_model_pattern, first_line)
        if match:
            car_info.brand = match.group(1).title()
            car_info.model = match.group(2).strip()
    
    # Извлечение года (4 цифры от 1980 до текущего года + 2)
    current_year = datetime.now().year
    year_pattern = r'\b(19[8-9]\d|20[0-2]\d)\b'
    year_match = re.search(year_pattern, text)
    if year_match:
        year = int(year_match.group(1))
        if 1980 <= year <= current_year + 2:
            car_info.year = year
    
    # Извлечение цены только в долларах
    price_patterns = [
        r'\$(\d{1,3}(?:[\s,]\d{3})*(?:\.\d{2})?)',  # $25,000 или $25 000
        r'(\d{1,3}(?:[\s,]\d{3})*(?:\.\d{2})?)\s*\$',  # 25,000$ или 25 000$
        r'(\d{1,3}(?:[\s,]?\d{3})*(?:\.\d{2})?)\s*(?:долл|dollar|USD)',  # 25000 долл
    ]
    
    for pattern in price_patterns:
        price_match = re.search(pattern, text, re.IGNORECASE)
        if price_match:
            price_str = price_match.group(1)
            if price_str:
                # Очищаем и парсим число
                clean_price = price_str.replace(' ', '').replace(',', '')
                try:
                    car_info.price = float(clean_price)
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

def create_car_description_prompt(car_info: CarInfo, custom_context: str = "") -> str:
    """
    Создает промпт для Perplexity API для генерации объявления о продаже китайского автомобиля
    
    Args:
        car_info: Информация об автомобиле
        custom_context: Дополнительный контекст
        
    Returns:
        Строка с промптом для API
    """
    
    # Технический промпт для генерации объявления
    prompt = f"""Создай техническое объявление для продажи автомобиля в формате HTML для Telegram. 

ИСХОДНЫЕ ДАННЫЕ:
- Марка/модель: {car_info.brand} {car_info.model}
- Год: {car_info.year}
- Пробег: {car_info.mileage} км
- Цена: {car_info.price}
- Двигатель: {car_info.engine_volume}
- КПП: {car_info.transmission}
- Привод: {car_info.drive_type}
- Комплектация: {car_info.trim}
- Цвет: {car_info.color}
- Состояние: {car_info.condition}

СТРУКТУРА ОБЪЯВЛЕНИЯ:
1. Заголовок: 🚗 <b>[Марка] [Модель] [Год]</b>
2. Custom ID: <b>Custom ID:</b> {car_info.custom_id or 'авто-онлайн'}
3. Технические характеристики в <blockquote>
4. Состояние и документы
5. Условия продажи (только онлайн, доставка, безнал)
6. Цена в долларах с пометкой (в Минске, без таможенных платежей)
7. Дополнительные детали (системы, мультимедиа, практичные опции)
8. Хештеги

ТРЕБОВАНИЯ ПО ФОРМАТИРОВАНИЮ:
- Используй ТОЛЬКО HTML-теги: <b></b>, <i></i>, <blockquote></blockquote>
- НЕ используй Markdown (**, *, #, -, >)
- Заголовки разделов делай жирными: <b>🔍 Технические характеристики:</b>
- Характеристики оборачивай в <blockquote>Двигатель: 2.0л
КПП: автомат</blockquote>
- Каждый раздел с новой строки

ПРИМЕР ПРАВИЛЬНОГО ФОРМАТИРОВАНИЯ:
🚗 <b>Geely Coolray 2023</b>
<b>Custom ID:</b> 947-175

<b>🔍 Технические характеристики:</b>
<blockquote>Двигатель: 2.0 л, бензин, 245 л.с.
КПП: Автоматическая
Привод: Полный
Пробег: 50,000 км</blockquote>

<b>📝 Состояние и документы:</b>
Состояние: Хорошее
Документы: В наличии

ТЕХНИЧЕСКИЕ ДЕТАЛИ К ДОБАВЛЕНИЮ:
- Точные характеристики двигателя и трансмиссии
- Системы безопасности и помощи водителю
- Мультимедиа и connectivity (CarPlay/Android Auto)
- Практичные опции (климат, подогревы, датчики)
- Размеры багажника и клиренс
- Экономичность (расход топлива)

{custom_context}

ВАЖНО: 
- Цена указана в долларах США (USD)
- НЕ используй никаких Markdown символов
- Все жирное форматирование через <b></b>
- Технические характеристики ТОЛЬКО в <blockquote></blockquote>

Создай краткое техническое объявление до 900 символов."""

    return prompt

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

def format_price_with_markup(car_info: CarInfo, markup_percentage: float = 15.0) -> str:
    """
    Форматирует цену с наценкой в долларах
    
    Args:
        car_info: Информация об автомобиле с ценой
        markup_percentage: Процент наценки
        
    Returns:
        Отформатированная цена с наценкой в долларах
    """
    if not car_info.price:
        return "Цена не указана"
    
    # Применяем наценку
    final_price = apply_markup_to_price(car_info.price, markup_percentage)
    
    # Форматируем в долларах
    return f"${final_price:,.0f}"

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