"""
Legacy Wrapper - обеспечение совместимости с существующим кодом
Предоставляет старый интерфейс для плавной миграции
"""

import os
from typing import Dict, Optional, List, Any, Union
from pathlib import Path
import logging

from .cloudinary_client import CloudinaryClient, CloudinaryConfig, CloudinaryUploadError, CloudinaryAPIError
from .image_manager import get_car_photos_urls as _get_car_photos_urls, get_car_photo_thumbnails as _get_car_photo_thumbnails

logger = logging.getLogger(__name__)

# Глобальный клиент для legacy функций
_legacy_client: Optional[CloudinaryClient] = None

def _get_legacy_client() -> Optional[CloudinaryClient]:
    """Получение или создание legacy клиента"""
    global _legacy_client
    if _legacy_client is None:
        try:
            config = CloudinaryConfig()
            # Проверяем, есть ли хотя бы минимальная конфигурация
            if config.cloudinary_url or (config.cloud_name and config.api_key and config.api_secret):
                _legacy_client = CloudinaryClient(config)
            else:
                # Нет конфигурации - возвращаем None для совместимости
                return None
        except Exception as e:
            logger.warning(f"Не удалось создать Cloudinary клиент: {e}")
            return None
    return _legacy_client

def upload_image_to_cloudinary(image_path: str, public_id: str = None) -> Optional[Dict[str, Any]]:
    """
    Legacy функция для загрузки изображения в Cloudinary
    Эмулирует поведение старой функции из app.core.cloudinary_uploader
    
    Args:
        image_path: Путь к локальному файлу изображения
        public_id: Уникальный идентификатор для файла в Cloudinary (опционально)
    
    Returns:
        Словарь с информацией о загруженном изображении от Cloudinary или None при ошибке
    """
    client = _get_legacy_client()
    
    # Проверяем конфигурацию (эмулируем старое поведение)
    cloudinary_url = os.getenv("CLOUDINARY_URL")
    cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME")
    
    if not cloudinary_url and not cloud_name:
        print("Ошибка: Cloudinary не сконфигурирован. Загрузка невозможна.")
        return None
    
    if client is None:
        print("Ошибка: Cloudinary не сконфигурирован. Загрузка невозможна.")
        return None
    
    try:
        upload_options = {}
        if public_id:
            upload_options['public_id'] = public_id
            upload_options['overwrite'] = True  # Соответствует старому поведению
        
        result = client.upload_image(
            image_path=image_path,
            **upload_options
        )
        
        print(f"Изображение {image_path} успешно загружено в Cloudinary. URL: {result.get('secure_url')}")
        return result
        
    except CloudinaryUploadError as e:
        print(f"Ошибка при загрузке изображения {image_path} в Cloudinary: {e}")
        return None
    except Exception as e:
        print(f"Ошибка при загрузке изображения {image_path} в Cloudinary: {e}")
        return None

def get_image_url_from_cloudinary(public_id: str, transformations: dict = None) -> Optional[str]:
    """
    Legacy функция для получения URL изображения из Cloudinary
    Эмулирует поведение старой функции из app.core.cloudinary_uploader
    
    Args:
        public_id: Уникальный идентификатор файла в Cloudinary
        transformations: Словарь с параметрами трансформации (опционально)
    
    Returns:
        URL изображения или None при ошибке
    """
    client = _get_legacy_client()
    
    # Проверяем конфигурацию (эмулируем старое поведение)
    cloudinary_url = os.getenv("CLOUDINARY_URL")
    cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME")
    
    if not cloudinary_url and not cloud_name:
        print("Ошибка: Cloudinary не сконфигурирован. Получение URL невозможно.")
        return None
    
    if client is None:
        print("Ошибка: Cloudinary не сконфигурирован. Получение URL невозможно.")
        return None
    
    try:
        url = client.get_image_url(
            public_id=public_id,
            transformations=transformations
        )
        return url
        
    except CloudinaryAPIError as e:
        print(f"Ошибка при получении URL для public_id {public_id} из Cloudinary: {e}")
        return None
    except Exception as e:
        print(f"Ошибка при получении URL для public_id {public_id} из Cloudinary: {e}")
        return None

def get_car_photos_urls(custom_id: str, count: int = 10) -> List[str]:
    """
    Legacy функция для получения списка URL фотографий автомобиля
    Эмулирует поведение старой функции из app.core.cloudinary_uploader
    
    Args:
        custom_id: Уникальный ID автомобиля
        count: Максимальное количество фотографий для поиска (по умолчанию 10)
    
    Returns:
        Список URL фотографий
    """
    # Проверяем конфигурацию (эмулируем старое поведение)
    cloudinary_url = os.getenv("CLOUDINARY_URL")
    cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME")
    
    if not cloudinary_url and not cloud_name:
        print("Ошибка: Cloudinary не сконфигурирован. Получение URL невозможно.")
        return []
    
    client = _get_legacy_client()
    if client is None:
        print("Ошибка: Cloudinary не сконфигурирован. Получение URL невозможно.")
        return []
    
    try:
        # Используем новую функцию без папки (как в старом коде)
        return _get_car_photos_urls(custom_id, count, folder="", client=client)
    except Exception as e:
        logger.error(f"Ошибка получения фотографий автомобиля {custom_id}: {e}")
        return []

def get_car_photo_thumbnails(custom_id: str, count: int = 10, width: int = 300, height: int = 200) -> List[str]:
    """
    Legacy функция для получения списка URL миниатюр фотографий автомобиля
    Эмулирует поведение старой функции из app.core.cloudinary_uploader
    
    Args:
        custom_id: Уникальный ID автомобиля
        count: Максимальное количество фотографий для поиска
        width: Ширина миниатюры
        height: Высота миниатюры
    
    Returns:
        Список URL миниатюр
    """
    # Проверяем конфигурацию (эмулируем старое поведение)
    cloudinary_url = os.getenv("CLOUDINARY_URL")
    cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME")
    
    if not cloudinary_url and not cloud_name:
        print("Ошибка: Cloudinary не сконфигурирован. Получение URL невозможно.")
        return []
    
    client = _get_legacy_client()
    if client is None:
        print("Ошибка: Cloudinary не сконфигурирован. Получение URL невозможно.")
        return []
    
    try:
        # Используем новую функцию без папки (как в старом коде)
        return _get_car_photo_thumbnails(
            custom_id, count, width, height, folder="", client=client
        )
    except Exception as e:
        logger.error(f"Ошибка получения миниатюр автомобиля {custom_id}: {e}")
        return []

# Дополнительные legacy функции для полной совместимости

def test_cloudinary_connection() -> bool:
    """
    Тестирование соединения с Cloudinary
    
    Returns:
        True если соединение работает, False в противном случае
    """
    client = _get_legacy_client()
    if client is None:
        return False
    
    return client.test_connection()

def get_cloudinary_upload_stats() -> Dict[str, Any]:
    """
    Получение статистики использования Cloudinary аккаунта
    
    Returns:
        Словарь со статистикой или пустой словарь при ошибке
    """
    client = _get_legacy_client()
    if client is None:
        return {}
    
    return client.get_upload_stats()

# Функции для эмуляции старого main блока

def _create_test_image() -> str:
    """Создание тестового изображения для совместимости"""
    test_path = "test.jpg"
    if os.path.exists(test_path):
        return test_path
    
    try:
        from PIL import Image
        img = Image.new('RGB', (60, 30), color='red')
        img.save(test_path)
        print("Создан тестовый файл test.jpg")
        return test_path
    except ImportError:
        print("PIL не установлен, не могу создать тестовый файл.")
        return ""
    except Exception as e:
        print(f"Не удалось создать тестовый файл: {e}")
        return ""

def run_legacy_test():
    """
    Запуск legacy теста (эмулирует старый main блок)
    """
    cloudinary_url = os.getenv("CLOUDINARY_URL")
    cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME")
    
    # Создаем тестовый файл если нет конфигурации
    if not cloudinary_url and not cloud_name and not os.path.exists("test.jpg"):
        test_image_path = _create_test_image()
        if not test_image_path:
            return
    
    if cloudinary_url or cloud_name:
        test_image_path = "test.jpg"
        if os.path.exists(test_image_path):
            print("=== Тестирование legacy Cloudinary wrapper ===")
            
            # 1. Загрузка изображения
            upload_result = upload_image_to_cloudinary(test_image_path, public_id="test_car_image")
            
            if upload_result:
                print(f"Результат загрузки: {upload_result}")
                uploaded_public_id = upload_result.get("public_id")
                
                # 2. Получение URL загруженного изображения
                image_url = get_image_url_from_cloudinary(uploaded_public_id)
                if image_url:
                    print(f"URL изображения: {image_url}")
                
                # 3. Получение URL с трансформациями
                transformed_image_url = get_image_url_from_cloudinary(
                    uploaded_public_id,
                    transformations={'width': 100, 'height': 100, 'crop': 'thumb'}
                )
                if transformed_image_url:
                    print(f"URL трансформированного изображения: {transformed_image_url}")
                    
                # 4. Тест соединения
                if test_cloudinary_connection():
                    print("✅ Тест соединения пройден")
                else:
                    print("❌ Тест соединения не пройден")
                    
                # 5. Статистика
                stats = get_cloudinary_upload_stats()
                if stats:
                    print(f"📊 Статистика: {stats}")
                    
            else:
                print("Загрузка тестового изображения не удалась.")
        else:
            print(f"Тестовый файл {test_image_path} не найден. Пропустим тест загрузки и получения URL.")
    else:
        print("CLOUDINARY_URL не установлен. Пропустим тест взаимодействия с Cloudinary.")

if __name__ == '__main__':
    run_legacy_test() 