"""
Модуль форматирования данных автомобилей для Storage API
Извлекает структурированные данные из текстов объявлений
"""

import re
from typing import Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def extract_car_details(text: str) -> Dict[str, Any]:
    """
    Извлекает детали автомобиля из текста с помощью регулярных выражений.
    
    Args:
        text: Текст объявления
        
    Returns:
        Словарь с деталями автомобиля: brand, model, year, price
    """
    details = {
        'brand': None,
        'model': None,
        'year': None,
        'price': None
    }
    
    if not text or not isinstance(text, str):
        return details
    
    logger.debug(f"Извлечение данных из текста: {text[:200]}...")
    
    # Паттерн 1: [Марка] [Модель] [Год] - формат Perplexity
    pattern1 = re.search(r'\[([^\]]+)\]\s*\[([^\]]+)\]\s*\[(\d{4})\]', text)
    if pattern1:
        details['brand'] = pattern1.group(1).strip()
        details['model'] = pattern1.group(2).strip()
        try:
            details['year'] = int(pattern1.group(3))
        except ValueError:
            pass
        logger.debug(f"Найдено (паттерн 1): {details['brand']} {details['model']} {details['year']}")
    
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
                logger.debug(f"Найдено (паттерн 2): {details['brand']} {details['model']} {details['year']}")
            except (ValueError, IndexError) as e:
                logger.error(f"Ошибка при извлечении года из текста: {e}")
    
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
                        logger.debug(f"Найдено (паттерн 3): {details['brand']} {details['model']} {details['year']}")
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
                logger.debug(f"Найдена цена: {details['price']}")
                break
            except (ValueError, TypeError):
                continue
    
    logger.debug(f"Итоговые данные: brand={details['brand']}, model={details['model']}, year={details['year']}, price={details['price']}")
    return details

def format_car_data_for_storage(
    custom_id: str,
    source_message_id: int,
    source_channel_name: str,
    description: str,
    cloudinary_urls: list,
    target_msg_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Форматирует данные автомобиля для сохранения в базе данных.
    
    Args:
        custom_id: Уникальный идентификатор объявления
        source_message_id: ID исходного сообщения
        source_channel_name: Название исходного канала
        description: Описание автомобиля
        cloudinary_urls: Список URL фотографий
        target_msg_id: ID сообщения в целевом канале
        
    Returns:
        Сформированный словарь для отправки в API
    """
    # Извлекаем детали автомобиля из описания
    car_details = extract_car_details(description)
    
    # Формируем финальный объект для API
    car_dict = {
        "custom_id": custom_id,
        "source_message_id": source_message_id,
        "source_channel_name": source_channel_name,
        "target_channel_message_id": target_msg_id,
        "brand": car_details.get('brand'),
        "model": car_details.get('model'),
        "year": car_details.get('year'),
        "price": car_details.get('price'),
        "description": description,
        "photos": cloudinary_urls,
        "status": 'available' if target_msg_id else 'error',
        "created_at": datetime.utcnow().isoformat()
    }
    
    logger.info(f"Сформированы данные для автомобиля {custom_id}: {car_details.get('brand')} {car_details.get('model')}")
    return car_dict 