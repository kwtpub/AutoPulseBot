"""
Cloudinary API Module - изолированный модуль для работы с Cloudinary CDN

Этот модуль предоставляет:
- Клиент для Cloudinary API
- Управление изображениями и трансформациями
- Batch загрузку и обработку
- Legacy wrapper для совместимости
- Конфигурацию и настройки
"""

# Публичное API модуля
from .cloudinary_client import CloudinaryClient, CloudinaryConfig
from .image_manager import (
    upload_single_image,
    get_image_url_with_transformations,
    get_car_photos_urls,
    get_car_photo_thumbnails,
    batch_upload_images,
    delete_image
)
from .legacy_wrapper import upload_image_to_cloudinary, get_image_url_from_cloudinary

# Удобные функции для быстрого использования
from .image_manager import upload_single_image as upload_image
from .image_manager import get_image_url_with_transformations as get_image_url

__all__ = [
    # Основные классы
    'CloudinaryClient',
    'CloudinaryConfig',
    
    # Управление изображениями
    'upload_single_image',
    'upload_image',  # Alias
    'get_image_url_with_transformations', 
    'get_image_url',  # Alias
    'get_car_photos_urls',
    'get_car_photo_thumbnails',
    'batch_upload_images',
    'delete_image',
    
    # Legacy совместимость
    'upload_image_to_cloudinary',
    'get_image_url_from_cloudinary',
]

# Версия модуля
__version__ = '1.0.0' 