"""
Cloudinary API Client - основной клиент для работы с Cloudinary CDN
Поддерживает различные конфигурации, трансформации и обработку ошибок
"""

import os
import asyncio
from dataclasses import dataclass
from typing import Dict, Optional, List, Any, Union
import logging
from pathlib import Path

try:
    import cloudinary
    import cloudinary.uploader
    import cloudinary.api
    from cloudinary.exceptions import Error as CloudinaryError
    CLOUDINARY_AVAILABLE = True
except ImportError:
    CLOUDINARY_AVAILABLE = False
    CloudinaryError = Exception

logger = logging.getLogger(__name__)

@dataclass
class CloudinaryConfig:
    """Конфигурация для Cloudinary API клиента"""
    cloud_name: Optional[str] = None
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    cloudinary_url: Optional[str] = None
    secure: bool = True
    max_file_size: int = 10 * 1024 * 1024  # 10MB по умолчанию
    allowed_formats: List[str] = None
    auto_tagging: bool = True
    overwrite: bool = True
    
    def __post_init__(self):
        if self.allowed_formats is None:
            self.allowed_formats = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp', 'tiff']
        
        # Если cloudinary_url не указан, попробуем получить из переменных окружения
        if not self.cloudinary_url:
            self.cloudinary_url = os.getenv("CLOUDINARY_URL")
        
        # Если отдельные параметры не указаны, попробуем получить из env
        if not self.cloud_name:
            self.cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME")
        if not self.api_key:
            self.api_key = os.getenv("CLOUDINARY_API_KEY")
        if not self.api_secret:
            self.api_secret = os.getenv("CLOUDINARY_API_SECRET")

# Специализированные исключения
class CloudinaryClientError(Exception):
    """Базовое исключение для Cloudinary клиента"""
    pass

class CloudinaryConfigError(CloudinaryClientError):
    """Ошибка конфигурации Cloudinary"""
    pass

class CloudinaryUploadError(CloudinaryClientError):
    """Ошибка загрузки в Cloudinary"""
    pass

class CloudinaryAPIError(CloudinaryClientError):
    """Ошибка API Cloudinary"""
    pass

class CloudinaryNetworkError(CloudinaryClientError):
    """Ошибка сети при работе с Cloudinary"""
    pass

class CloudinaryClient:
    """
    Современный клиент для Cloudinary API с улучшенной обработкой ошибок
    и гибкой конфигурацией
    """
    
    def __init__(self, config: CloudinaryConfig):
        """
        Инициализация клиента Cloudinary
        
        Args:
            config: Конфигурация CloudinaryConfig
        """
        if not CLOUDINARY_AVAILABLE:
            raise CloudinaryConfigError(
                "Cloudinary библиотека не установлена. Выполните: pip install cloudinary"
            )
        
        self.config = config
        self._configure_cloudinary()
        
    def _configure_cloudinary(self):
        """Настройка Cloudinary с проверкой конфигурации"""
        try:
            if self.config.cloudinary_url:
                # Конфигурация через URL
                cloudinary.config(
                    cloudinary_url=self.config.cloudinary_url,
                    secure=self.config.secure
                )
            elif all([self.config.cloud_name, self.config.api_key, self.config.api_secret]):
                # Конфигурация через отдельные параметры
                cloudinary.config(
                    cloud_name=self.config.cloud_name,
                    api_key=self.config.api_key,
                    api_secret=self.config.api_secret,
                    secure=self.config.secure
                )
            else:
                raise CloudinaryConfigError(
                    "Cloudinary не сконфигурирован. "
                    "Установите CLOUDINARY_URL или отдельные параметры (cloud_name, api_key, api_secret)"
                )
                
            # Проверяем конфигурацию
            self._validate_config()
            logger.info("Cloudinary клиент успешно сконфигурирован")
            
        except CloudinaryError as e:
            raise CloudinaryConfigError(f"Ошибка конфигурации Cloudinary: {e}")
    
    def _validate_config(self):
        """Проверка валидности конфигурации"""
        try:
            # Простой тест конфигурации через получение информации о папках
            cloudinary.api.root_folders(max_results=1)
        except CloudinaryError as e:
            if "Invalid API key" in str(e) or "Unauthorized" in str(e):
                raise CloudinaryConfigError("Неверный API ключ или секрет")
            elif "Not Found" in str(e):
                raise CloudinaryConfigError("Неверное имя облака (cloud_name)")
            else:
                logger.warning(f"Не удалось полностью проверить конфигурацию: {e}")
    
    def upload_image(
        self, 
        image_path: Union[str, Path], 
        public_id: Optional[str] = None,
        folder: Optional[str] = None,
        tags: Optional[List[str]] = None,
        transformations: Optional[Dict] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Загрузка изображения в Cloudinary
        
        Args:
            image_path: Путь к файлу изображения
            public_id: Уникальный идентификатор (опционально)
            folder: Папка в Cloudinary (опционально)
            tags: Теги для изображения (опционально)
            transformations: Трансформации при загрузке (опционально)
            **kwargs: Дополнительные параметры для Cloudinary
        
        Returns:
            Dict с информацией о загруженном изображении
        
        Raises:
            CloudinaryUploadError: При ошибке загрузки
            CloudinaryConfigError: При проблемах с конфигурацией
        """
        try:
            image_path = Path(image_path)
            
            # Проверки перед загрузкой
            self._validate_image_file(image_path)
            
            # Подготовка параметров загрузки
            upload_options = {
                'overwrite': self.config.overwrite,
                **kwargs
            }
            
            if public_id:
                upload_options['public_id'] = public_id
            
            if folder:
                upload_options['folder'] = folder
                
            if tags:
                upload_options['tags'] = tags
                
            if transformations:
                upload_options['transformation'] = transformations
                
            if self.config.auto_tagging:
                existing_tags = upload_options.get('tags', [])
                auto_tags = self._generate_auto_tags(image_path)
                upload_options['tags'] = list(set(existing_tags + auto_tags))
            
            # Загрузка
            result = cloudinary.uploader.upload(str(image_path), **upload_options)
            
            logger.info(f"Изображение {image_path.name} успешно загружено. URL: {result.get('secure_url')}")
            return result
            
        except CloudinaryError as e:
            error_msg = f"Ошибка Cloudinary API при загрузке {image_path}: {e}"
            logger.error(error_msg)
            raise CloudinaryUploadError(error_msg)
        except Exception as e:
            error_msg = f"Неожиданная ошибка при загрузке {image_path}: {e}"
            logger.error(error_msg)
            raise CloudinaryUploadError(error_msg)
    
    def _validate_image_file(self, image_path: Path):
        """Валидация файла изображения"""
        if not image_path.exists():
            raise CloudinaryUploadError(f"Файл не найден: {image_path}")
        
        if image_path.stat().st_size > self.config.max_file_size:
            raise CloudinaryUploadError(
                f"Файл слишком большой: {image_path.stat().st_size} bytes, "
                f"максимум: {self.config.max_file_size} bytes"
            )
        
        file_extension = image_path.suffix.lower().lstrip('.')
        if file_extension not in self.config.allowed_formats:
            raise CloudinaryUploadError(
                f"Неподдерживаемый формат: {file_extension}. "
                f"Поддерживаются: {', '.join(self.config.allowed_formats)}"
            )
    
    def _generate_auto_tags(self, image_path: Path) -> List[str]:
        """Генерация автоматических тегов на основе пути файла"""
        tags = []
        
        # Тег на основе расширения файла
        extension = image_path.suffix.lower().lstrip('.')
        if extension:
            tags.append(f"format_{extension}")
        
        # Тег на основе размера файла
        size_mb = image_path.stat().st_size / (1024 * 1024)
        if size_mb < 1:
            tags.append("small_file")
        elif size_mb < 5:
            tags.append("medium_file")
        else:
            tags.append("large_file")
        
        return tags
    
    def get_image_url(
        self, 
        public_id: str, 
        transformations: Optional[Dict] = None,
        secure: Optional[bool] = None
    ) -> str:
        """
        Получение URL изображения с возможными трансформациями
        
        Args:
            public_id: Идентификатор изображения в Cloudinary
            transformations: Параметры трансформации (опционально)
            secure: Использовать HTTPS (опционально, по умолчанию из конфига)
        
        Returns:
            URL изображения
        
        Raises:
            CloudinaryAPIError: При ошибке API
        """
        try:
            options = {}
            if secure is not None:
                options['secure'] = secure
            elif self.config.secure:
                options['secure'] = True
            
            if transformations:
                options['transformation'] = transformations
            
            url = cloudinary.CloudinaryImage(public_id).build_url(**options)
            return url
            
        except CloudinaryError as e:
            error_msg = f"Ошибка получения URL для {public_id}: {e}"
            logger.error(error_msg)
            raise CloudinaryAPIError(error_msg)
    
    def delete_image(self, public_id: str) -> Dict[str, Any]:
        """
        Удаление изображения из Cloudinary
        
        Args:
            public_id: Идентификатор изображения
        
        Returns:
            Результат операции удаления
        
        Raises:
            CloudinaryAPIError: При ошибке API
        """
        try:
            result = cloudinary.uploader.destroy(public_id)
            logger.info(f"Изображение {public_id} удалено из Cloudinary")
            return result
        except CloudinaryError as e:
            error_msg = f"Ошибка удаления изображения {public_id}: {e}"
            logger.error(error_msg)
            raise CloudinaryAPIError(error_msg)
    
    def batch_upload(
        self, 
        image_paths: List[Union[str, Path]], 
        folder: Optional[str] = None,
        prefix: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Batch загрузка нескольких изображений
        
        Args:
            image_paths: Список путей к изображениям
            folder: Папка в Cloudinary для всех изображений
            prefix: Префикс для public_id всех изображений
            tags: Общие теги для всех изображений
        
        Returns:
            Список результатов загрузки
        """
        results = []
        
        for i, path in enumerate(image_paths):
            try:
                public_id = None
                if prefix:
                    public_id = f"{prefix}_{i+1}"
                
                result = self.upload_image(
                    image_path=path,
                    public_id=public_id,
                    folder=folder,
                    tags=tags
                )
                results.append(result)
                
            except CloudinaryUploadError as e:
                logger.error(f"Ошибка загрузки файла {path}: {e}")
                results.append({"error": str(e), "file": str(path)})
        
        return results
    
    def get_upload_stats(self) -> Dict[str, Any]:
        """
        Получение статистики использования Cloudinary
        
        Returns:
            Статистика аккаунта
        """
        try:
            usage = cloudinary.api.usage()
            return {
                "credits_used": usage.get("credits", {}).get("used", 0),
                "credits_limit": usage.get("credits", {}).get("limit", 0),
                "storage_used": usage.get("storage", {}).get("used", 0),
                "storage_limit": usage.get("storage", {}).get("limit", 0),
                "bandwidth_used": usage.get("bandwidth", {}).get("used", 0),
                "bandwidth_limit": usage.get("bandwidth", {}).get("limit", 0),
            }
        except CloudinaryError as e:
            logger.error(f"Ошибка получения статистики: {e}")
            return {}
    
    def test_connection(self) -> bool:
        """
        Тестирование соединения с Cloudinary
        
        Returns:
            True если соединение работает
        """
        try:
            # Простой тест - получение списка папок
            cloudinary.api.root_folders(max_results=1)
            return True
        except Exception as e:
            logger.error(f"Тест соединения не пройден: {e}")
            return False
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        # Cloudinary не требует явного закрытия соединений
        pass 