"""
Обертка для совместимости с существующим кодом
Заменяет функции send_to_node и check_duplicate_car
"""

from .database_client import check_car_duplicate, get_client
from .data_formatter import format_car_data_for_storage
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

def send_car_to_node(car_data_dict):
    """
    Обертка для замены старой функции send_to_node
    Совместима с существующим кодом
    """
    try:
        client = get_client()
        
        # Создаем объект CarData из словаря
        from .database_client import CarData
        car_data = CarData(
            custom_id=car_data_dict.get('custom_id'),
            source_message_id=car_data_dict.get('source_message_id'),
            source_channel_name=car_data_dict.get('source_channel_name'),
            brand=car_data_dict.get('brand'),
            model=car_data_dict.get('model'),
            year=car_data_dict.get('year'),
            price=car_data_dict.get('price'),
            description=car_data_dict.get('description'),
            photos=car_data_dict.get('photos', []),
            status=car_data_dict.get('status', 'available'),
            target_channel_message_id=car_data_dict.get('target_channel_message_id')
        )
        
        # Используем прямой вызов клиента вместо промежуточной функции
        result = client.save_car(car_data)
        
        if result is not None:
            return {'message': 'Car saved successfully'}
        else:
            return {'error': 'Failed to save car'}
            
    except Exception as e:
        logger.error(f"Ошибка в send_car_to_node: {e}")
        return {'error': str(e)}

def check_duplicate_car(source_message_id, source_channel_name):
    """
    Обертка для замены старой функции check_duplicate_car
    Совместима с существующим кодом
    """
    try:
        result = check_car_duplicate(source_message_id, source_channel_name)
        return result
        
    except Exception as e:
        logger.error(f"Ошибка в check_duplicate_car: {e}")
        return None

def save_car_with_formatting(
    custom_id: str,
    source_message_id: int,
    source_channel_name: str,
    description: str,
    cloudinary_urls: list,
    target_msg_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Новая функция для сохранения автомобиля с автоматическим форматированием.
    Использует внутренний форматтер Storage API.
    """
    try:
        # Форматируем данные через Storage API
        car_data = format_car_data_for_storage(
            custom_id=custom_id,
            source_message_id=source_message_id,
            source_channel_name=source_channel_name,
            description=description,
            cloudinary_urls=cloudinary_urls,
            target_msg_id=target_msg_id
        )
        
        # Сохраняем через Storage API
        return send_car_to_node(car_data)
        
    except Exception as e:
        logger.error(f"Ошибка в save_car_with_formatting: {e}")
        return {
            'message': f'Error: {str(e)}',
            'success': False
        }

def test_database_connection():
    """
    Тестирование подключения к базе данных
    """
    try:
        client = get_client()
        is_healthy = client.health_check()
        
        if is_healthy:
            logger.info("✅ База данных доступна")
            return True
        else:
            logger.warning("⚠️ База данных недоступна")
            return False
            
    except Exception as e:
        logger.error(f"❌ Ошибка подключения к базе данных: {e}")
        return False 