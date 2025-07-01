"""
Image Manager - высокоуровневые функции для работы с изображениями в Cloudinary
Специализированные функции для автомобильных фотографий и batch операций
"""

from typing import List, Dict, Optional, Union, Any
from pathlib import Path
import logging

from .cloudinary_client import CloudinaryClient, CloudinaryConfig, CloudinaryUploadError

logger = logging.getLogger(__name__)

# Глобальный клиент для использования в функциях
_default_client: Optional[CloudinaryClient] = None

def _get_default_client() -> CloudinaryClient:
    """Получение или создание клиента по умолчанию"""
    global _default_client
    if _default_client is None:
        config = CloudinaryConfig()  # Будет использовать переменные окружения
        _default_client = CloudinaryClient(config)
    return _default_client

def upload_single_image(
    image_path: Union[str, Path],
    public_id: Optional[str] = None,
    folder: Optional[str] = None,
    tags: Optional[List[str]] = None,
    transformations: Optional[Dict] = None,
    client: Optional[CloudinaryClient] = None
) -> Dict[str, Any]:
    """
    Загрузка одного изображения в Cloudinary
    
    Args:
        image_path: Путь к изображению
        public_id: Уникальный идентификатор (опционально)
        folder: Папка в Cloudinary (опционально)
        tags: Теги для изображения (опционально)
        transformations: Трансформации при загрузке (опционально)
        client: Клиент Cloudinary (опционально, будет создан автоматически)
    
    Returns:
        Результат загрузки от Cloudinary API
    
    Raises:
        CloudinaryUploadError: При ошибке загрузки
    """
    if client is None:
        client = _get_default_client()
    
    return client.upload_image(
        image_path=image_path,
        public_id=public_id,
        folder=folder,
        tags=tags,
        transformations=transformations
    )

def get_image_url_with_transformations(
    public_id: str,
    transformations: Optional[Dict] = None,
    secure: bool = True,
    client: Optional[CloudinaryClient] = None
) -> str:
    """
    Получение URL изображения с трансформациями
    
    Args:
        public_id: Идентификатор изображения в Cloudinary
        transformations: Параметры трансформации (опционально)
        secure: Использовать HTTPS (по умолчанию True)
        client: Клиент Cloudinary (опционально)
    
    Returns:
        URL изображения
    """
    if client is None:
        client = _get_default_client()
    
    return client.get_image_url(
        public_id=public_id,
        transformations=transformations,
        secure=secure
    )

def batch_upload_images(
    image_paths: List[Union[str, Path]],
    folder: Optional[str] = None,
    prefix: Optional[str] = None,
    tags: Optional[List[str]] = None,
    client: Optional[CloudinaryClient] = None
) -> List[Dict[str, Any]]:
    """
    Batch загрузка нескольких изображений
    
    Args:
        image_paths: Список путей к изображениям
        folder: Папка в Cloudinary для всех изображений
        prefix: Префикс для public_id всех изображений
        tags: Общие теги для всех изображений
        client: Клиент Cloudinary (опционально)
    
    Returns:
        Список результатов загрузки
    """
    if client is None:
        client = _get_default_client()
    
    return client.batch_upload(
        image_paths=image_paths,
        folder=folder,
        prefix=prefix,
        tags=tags
    )

def delete_image(
    public_id: str,
    client: Optional[CloudinaryClient] = None
) -> Dict[str, Any]:
    """
    Удаление изображения из Cloudinary
    
    Args:
        public_id: Идентификатор изображения
        client: Клиент Cloudinary (опционально)
    
    Returns:
        Результат операции удаления
    """
    if client is None:
        client = _get_default_client()
    
    return client.delete_image(public_id)

# Специализированные функции для автомобильных фотографий

def upload_car_photos(
    image_paths: List[Union[str, Path]],
    custom_id: str,
    folder: str = "cars",
    client: Optional[CloudinaryClient] = None
) -> List[Dict[str, Any]]:
    """
    Загрузка фотографий автомобиля с автоматическими ID
    
    Args:
        image_paths: Список путей к фотографиям автомобиля
        custom_id: Уникальный ID автомобиля
        folder: Папка в Cloudinary (по умолчанию "cars")
        client: Клиент Cloudinary (опционально)
    
    Returns:
        Список результатов загрузки
    """
    if client is None:
        client = _get_default_client()
    
    results = []
    for i, image_path in enumerate(image_paths, 1):
        public_id = f"car_{custom_id}_{i}"
        tags = ["car", f"car_id_{custom_id}", f"photo_{i}"]
        
        try:
            result = client.upload_image(
                image_path=image_path,
                public_id=public_id,
                folder=folder,
                tags=tags
            )
            results.append(result)
            logger.info(f"Загружено фото {i} для автомобиля {custom_id}")
        except CloudinaryUploadError as e:
            logger.error(f"Ошибка загрузки фото {i} для автомобиля {custom_id}: {e}")
            results.append({"error": str(e), "file": str(image_path)})
    
    return results

def get_car_photos_urls(
    custom_id: str,
    count: int = 10,
    folder: str = "cars",
    client: Optional[CloudinaryClient] = None
) -> List[str]:
    """
    Получение URL всех фотографий автомобиля
    
    Args:
        custom_id: Уникальный ID автомобиля
        count: Максимальное количество фотографий для поиска (по умолчанию 10)
        folder: Папка в Cloudinary (по умолчанию "cars")
        client: Клиент Cloudinary (опционально)
    
    Returns:
        Список URL фотографий
    """
    if client is None:
        client = _get_default_client()
    
    photo_urls = []
    for i in range(1, count + 1):
        public_id = f"{folder}/car_{custom_id}_{i}" if folder else f"car_{custom_id}_{i}"
        
        try:
            url = client.get_image_url(public_id)
            if url:
                photo_urls.append(url)
        except Exception:
            # Если фото с таким ID не найдено, прекращаем поиск
            break
    
    return photo_urls

def get_car_photo_thumbnails(
    custom_id: str,
    count: int = 10,
    width: int = 300,
    height: int = 200,
    folder: str = "cars",
    client: Optional[CloudinaryClient] = None
) -> List[str]:
    """
    Получение URL миниатюр всех фотографий автомобиля
    
    Args:
        custom_id: Уникальный ID автомобиля
        count: Максимальное количество фотографий для поиска
        width: Ширина миниатюры (по умолчанию 300)
        height: Высота миниатюры (по умолчанию 200)
        folder: Папка в Cloudinary (по умолчанию "cars")
        client: Клиент Cloudinary (опционально)
    
    Returns:
        Список URL миниатюр
    """
    if client is None:
        client = _get_default_client()
    
    thumbnail_urls = []
    transformations = {
        'width': width,
        'height': height,
        'crop': 'fill',
        'quality': 'auto',
        'fetch_format': 'auto'
    }
    
    for i in range(1, count + 1):
        public_id = f"{folder}/car_{custom_id}_{i}" if folder else f"car_{custom_id}_{i}"
        
        try:
            url = client.get_image_url(
                public_id=public_id,
                transformations=transformations
            )
            if url:
                thumbnail_urls.append(url)
        except Exception:
            # Если фото с таким ID не найдено, прекращаем поиск
            break
    
    return thumbnail_urls

def create_car_gallery(
    custom_id: str,
    width: int = 800,
    height: int = 600,
    folder: str = "cars",
    client: Optional[CloudinaryClient] = None
) -> Dict[str, List[str]]:
    """
    Создание галереи автомобиля с фотографиями разных размеров
    
    Args:
        custom_id: Уникальный ID автомобиля
        width: Ширина больших изображений
        height: Высота больших изображений
        folder: Папка в Cloudinary
        client: Клиент Cloudinary (опционально)
    
    Returns:
        Словарь с URL оригинальных изображений, больших и миниатюр
    """
    if client is None:
        client = _get_default_client()
    
    # Получаем оригинальные URL
    original_urls = get_car_photos_urls(custom_id, folder=folder, client=client)
    
    # Создаем большие изображения
    large_urls = []
    for i in range(1, len(original_urls) + 1):
        public_id = f"{folder}/car_{custom_id}_{i}" if folder else f"car_{custom_id}_{i}"
        transformations = {
            'width': width,
            'height': height,
            'crop': 'limit',
            'quality': 'auto',
            'fetch_format': 'auto'
        }
        
        try:
            url = client.get_image_url(
                public_id=public_id,
                transformations=transformations
            )
            large_urls.append(url)
        except Exception:
            break
    
    # Получаем миниатюры
    thumbnail_urls = get_car_photo_thumbnails(
        custom_id, 
        count=len(original_urls),
        folder=folder,
        client=client
    )
    
    return {
        "original": original_urls,
        "large": large_urls,
        "thumbnails": thumbnail_urls,
        "count": len(original_urls)
    }

def optimize_car_photo_for_web(
    public_id: str,
    max_width: int = 1200,
    quality: str = "auto",
    format: str = "auto",
    client: Optional[CloudinaryClient] = None
) -> str:
    """
    Получение оптимизированного для веба URL фотографии автомобиля
    
    Args:
        public_id: Идентификатор изображения
        max_width: Максимальная ширина (по умолчанию 1200)
        quality: Качество изображения (по умолчанию "auto")
        format: Формат изображения (по умолчанию "auto")
        client: Клиент Cloudinary (опционально)
    
    Returns:
        Оптимизированный URL изображения
    """
    if client is None:
        client = _get_default_client()
    
    transformations = {
        'width': max_width,
        'crop': 'limit',
        'quality': quality,
        'fetch_format': format,
        'flags': 'progressive'
    }
    
    return client.get_image_url(
        public_id=public_id,
        transformations=transformations
    )

def delete_car_photos(
    custom_id: str,
    count: int = 10,
    folder: str = "cars",
    client: Optional[CloudinaryClient] = None
) -> List[Dict[str, Any]]:
    """
    Удаление всех фотографий автомобиля
    
    Args:
        custom_id: Уникальный ID автомобиля
        count: Максимальное количество фотографий для удаления
        folder: Папка в Cloudinary
        client: Клиент Cloudinary (опционально)
    
    Returns:
        Список результатов удаления
    """
    if client is None:
        client = _get_default_client()
    
    results = []
    for i in range(1, count + 1):
        public_id = f"{folder}/car_{custom_id}_{i}" if folder else f"car_{custom_id}_{i}"
        
        try:
            result = client.delete_image(public_id)
            results.append(result)
            logger.info(f"Удалено фото {i} для автомобиля {custom_id}")
        except Exception as e:
            logger.error(f"Ошибка удаления фото {i} для автомобиля {custom_id}: {e}")
            results.append({"error": str(e), "public_id": public_id})
    
    return results

# Функции для работы с трансформациями

def create_responsive_image_set(
    public_id: str,
    breakpoints: Optional[List[int]] = None,
    client: Optional[CloudinaryClient] = None
) -> Dict[str, str]:
    """
    Создание набора адаптивных изображений для разных экранов
    
    Args:
        public_id: Идентификатор изображения
        breakpoints: Список ширин для создания версий (опционально)
        client: Клиент Cloudinary (опционально)
    
    Returns:
        Словарь с URL для разных размеров экрана
    """
    if client is None:
        client = _get_default_client()
    
    if breakpoints is None:
        breakpoints = [320, 480, 768, 1024, 1200, 1920]
    
    responsive_urls = {}
    
    for width in breakpoints:
        transformations = {
            'width': width,
            'crop': 'limit',
            'quality': 'auto',
            'fetch_format': 'auto'
        }
        
        url = client.get_image_url(
            public_id=public_id,
            transformations=transformations
        )
        responsive_urls[f"{width}w"] = url
    
    return responsive_urls 