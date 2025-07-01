import requests
import json
import os
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class CarData:
    """Структура данных автомобиля"""
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

class DatabaseClient:
    """
    Изолированный клиент для работы с базой данных через Node.js API
    Этот класс НЕ ТРОГАЕМ - он работает автономно!
    """
    
    def __init__(self, base_url: str = "http://localhost:3001"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'TelegramBot-StorageAPI/1.0'
        })
    
    def health_check(self) -> bool:
        """Проверка работы API"""
        try:
            response = self.session.get(f"{self.base_url}/api/health", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
    
    def save_car(self, car_data: CarData) -> Optional[Dict[str, Any]]:
        """
        Сохранение автомобиля в базу данных
        Возвращает данные сохраненного авто или None при ошибке
        """
        try:
            # Подготавливаем данные для отправки
            payload = {
                'custom_id': car_data.custom_id,
                'source_message_id': car_data.source_message_id,
                'source_channel_name': car_data.source_channel_name,
                'brand': car_data.brand,
                'model': car_data.model,
                'year': car_data.year,
                'price': car_data.price,
                'description': car_data.description,
                'photos': car_data.photos or [],
                'status': car_data.status,
                'target_channel_message_id': car_data.target_channel_message_id
            }
            
            logger.info(f"💾 Сохранение автомобиля: {car_data.custom_id}")
            
            response = self.session.post(
                f"{self.base_url}/api/cars",
                json=payload,
                timeout=10
            )
            
            if response.status_code in [200, 201]:  # 200 OK или 201 Created
                result = response.json()
                logger.info(f"✅ Автомобиль сохранен: {car_data.custom_id}")
                return result
            else:
                logger.error(f"❌ Ошибка сохранения {car_data.custom_id}: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Исключение при сохранении {car_data.custom_id}: {e}")
            return None
    
    def check_duplicate(self, source_message_id: int, source_channel_name: str) -> Optional[Dict[str, Any]]:
        """
        Проверка дубликата по ID сообщения и каналу
        Возвращает данные существующего авто или None
        """
        try:
            url = f"{self.base_url}/api/cars/check-duplicate/{source_message_id}/{source_channel_name}"
            
            response = self.session.get(url, timeout=5)
            
            if response.status_code == 200:
                result = response.json()
                if result:
                    logger.info(f"🔍 Найден дубликат: {result.get('custom_id')}")
                    return result
                else:
                    logger.info(f"🆕 Дубликат не найден для {source_message_id}")
                    return None
            else:
                logger.warning(f"⚠️ Ошибка проверки дубликата: {response.status_code}")
                return None
                
        except Exception as e:
            logger.warning(f"⚠️ Исключение при проверке дубликата: {e}")
            # При ошибке возвращаем None (как будто дубликата нет)
            return None
    
    def get_car(self, custom_id: str) -> Optional[Dict[str, Any]]:
        """Получение автомобиля по custom_id"""
        try:
            response = self.session.get(f"{self.base_url}/api/cars/{custom_id}", timeout=5)
            
            if response.status_code == 200:
                return response.json()
            else:
                return None
                
        except Exception as e:
            logger.error(f"Ошибка получения автомобиля {custom_id}: {e}")
            return None
    
    def get_all_cars(self, limit: int = 10, offset: int = 0) -> Optional[Dict[str, Any]]:
        """Получение списка автомобилей с пагинацией"""
        try:
            params = {'limit': limit, 'offset': offset}
            response = self.session.get(f"{self.base_url}/api/cars", params=params, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            else:
                return None
                
        except Exception as e:
            logger.error(f"Ошибка получения списка автомобилей: {e}")
            return None

# Глобальный экземпляр клиента
_client = None

def get_client() -> DatabaseClient:
    """Получение глобального экземпляра клиента базы данных"""
    global _client
    if _client is None:
        _client = DatabaseClient()
    return _client

# Удалена дублирующая функция save_car_to_db - теперь используется прямой вызов в legacy_wrapper

def check_car_duplicate(source_message_id: int, source_channel_name: str) -> Optional[Dict[str, Any]]:
    """
    Упрощенная функция для проверки дубликатов
    """
    try:
        client = get_client()
        return client.check_duplicate(source_message_id, source_channel_name)
    except Exception as e:
        logger.error(f"Ошибка в check_car_duplicate: {e}")
        return None 