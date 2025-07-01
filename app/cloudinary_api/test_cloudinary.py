"""
Тесты для Cloudinary API модуля
Проверяет функциональность клиента, управления изображениями и legacy совместимости
"""

import pytest
import os
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import tempfile

from .cloudinary_client import (
    CloudinaryClient, 
    CloudinaryConfig,
    CloudinaryClientError,
    CloudinaryConfigError,
    CloudinaryUploadError,
    CloudinaryAPIError
)
from .image_manager import (
    upload_single_image,
    get_image_url_with_transformations,
    batch_upload_images,
    upload_car_photos,
    get_car_photos_urls,
    get_car_photo_thumbnails,
    create_car_gallery,
    delete_car_photos
)
from .legacy_wrapper import (
    upload_image_to_cloudinary,
    get_image_url_from_cloudinary,
    get_car_photos_urls as legacy_get_car_photos_urls,
    test_cloudinary_connection
)

class TestCloudinaryConfig:
    """Тесты для CloudinaryConfig"""
    
    def test_config_creation_with_defaults(self):
        """Тест создания конфигурации с настройками по умолчанию"""
        config = CloudinaryConfig()
        assert config.secure is True
        assert config.max_file_size == 10 * 1024 * 1024
        assert 'jpg' in config.allowed_formats
        assert config.auto_tagging is True
    
    def test_config_creation_with_custom_values(self):
        """Тест создания конфигурации с пользовательскими значениями"""
        config = CloudinaryConfig(
            cloud_name="test_cloud",
            api_key="test_key",
            api_secret="test_secret",
            secure=False,
            max_file_size=5 * 1024 * 1024
        )
        assert config.cloud_name == "test_cloud"
        assert config.api_key == "test_key"
        assert config.api_secret == "test_secret"
        assert config.secure is False
        assert config.max_file_size == 5 * 1024 * 1024
    
    @patch.dict(os.environ, {
        'CLOUDINARY_CLOUD_NAME': 'env_cloud',
        'CLOUDINARY_API_KEY': 'env_key',
        'CLOUDINARY_API_SECRET': 'env_secret'
    })
    def test_config_from_environment(self):
        """Тест получения конфигурации из переменных окружения"""
        config = CloudinaryConfig()
        assert config.cloud_name == 'env_cloud'
        assert config.api_key == 'env_key'
        assert config.api_secret == 'env_secret'

class TestCloudinaryClient:
    """Тесты для CloudinaryClient"""
    
    def setup_method(self):
        """Настройка для каждого теста"""
        self.config = CloudinaryConfig(
            cloud_name="test_cloud",
            api_key="test_key",
            api_secret="test_secret"
        )
        
    @patch('app.cloudinary_api.cloudinary_client.CLOUDINARY_AVAILABLE', False)
    def test_client_creation_without_cloudinary_library(self):
        """Тест создания клиента без установленной библиотеки Cloudinary"""
        with pytest.raises(CloudinaryConfigError, match="Cloudinary библиотека не установлена"):
            CloudinaryClient(self.config)
    
    @patch('app.cloudinary_api.cloudinary_client.CLOUDINARY_AVAILABLE', True)
    @patch('app.cloudinary_api.cloudinary_client.cloudinary')
    def test_client_creation_success(self, mock_cloudinary):
        """Тест успешного создания клиента"""
        mock_cloudinary.api.root_folders.return_value = {"folders": []}
        
        client = CloudinaryClient(self.config)
        assert client.config == self.config
    
    @patch('app.cloudinary_api.cloudinary_client.CLOUDINARY_AVAILABLE', True)
    @patch('app.cloudinary_api.cloudinary_client.cloudinary')
    def test_client_config_validation_failure(self, mock_cloudinary):
        """Тест неудачной валидации конфигурации"""
        mock_cloudinary.api.root_folders.side_effect = Exception("Invalid API key")
        
        with pytest.raises(CloudinaryConfigError):
            CloudinaryClient(self.config)
    
    @patch('app.cloudinary_api.cloudinary_client.CLOUDINARY_AVAILABLE', True)
    @patch('app.cloudinary_api.cloudinary_client.cloudinary')
    def test_upload_image_success(self, mock_cloudinary):
        """Тест успешной загрузки изображения"""
        # Мок для валидации
        mock_cloudinary.api.root_folders.return_value = {"folders": []}
        
        # Мок для загрузки
        mock_upload_result = {
            "public_id": "test_image",
            "secure_url": "https://cloudinary.com/test_image.jpg",
            "width": 800,
            "height": 600
        }
        mock_cloudinary.uploader.upload.return_value = mock_upload_result
        
        client = CloudinaryClient(self.config)
        
        # Создаем временный файл изображения
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
            tmp_file.write(b"fake image data")
            tmp_path = tmp_file.name
        
        try:
            result = client.upload_image(tmp_path, public_id="test_image")
            assert result == mock_upload_result
            assert result["public_id"] == "test_image"
        finally:
            os.unlink(tmp_path)
    
    @patch('app.cloudinary_api.cloudinary_client.CLOUDINARY_AVAILABLE', True)
    @patch('app.cloudinary_api.cloudinary_client.cloudinary')
    def test_get_image_url_success(self, mock_cloudinary):
        """Тест успешного получения URL изображения"""
        mock_cloudinary.api.root_folders.return_value = {"folders": []}
        
        # Мок для CloudinaryImage
        mock_image = MagicMock()
        mock_image.build_url.return_value = "https://cloudinary.com/test_image.jpg"
        mock_cloudinary.CloudinaryImage.return_value = mock_image
        
        client = CloudinaryClient(self.config)
        url = client.get_image_url("test_image")
        
        assert url == "https://cloudinary.com/test_image.jpg"
        mock_cloudinary.CloudinaryImage.assert_called_with("test_image")
    
    @patch('app.cloudinary_api.cloudinary_client.CLOUDINARY_AVAILABLE', True) 
    @patch('app.cloudinary_api.cloudinary_client.cloudinary')
    def test_delete_image_success(self, mock_cloudinary):
        """Тест успешного удаления изображения"""
        mock_cloudinary.api.root_folders.return_value = {"folders": []}
        mock_cloudinary.uploader.destroy.return_value = {"result": "ok"}
        
        client = CloudinaryClient(self.config)
        result = client.delete_image("test_image")
        
        assert result == {"result": "ok"}
        mock_cloudinary.uploader.destroy.assert_called_with("test_image")
    
    @patch('app.cloudinary_api.cloudinary_client.CLOUDINARY_AVAILABLE', True)
    @patch('app.cloudinary_api.cloudinary_client.cloudinary')
    def test_test_connection_success(self, mock_cloudinary):
        """Тест успешного тестирования соединения"""
        mock_cloudinary.api.root_folders.return_value = {"folders": []}
        
        client = CloudinaryClient(self.config)
        assert client.test_connection() is True
    
    @patch('app.cloudinary_api.cloudinary_client.CLOUDINARY_AVAILABLE', True)
    @patch('app.cloudinary_api.cloudinary_client.cloudinary')
    def test_test_connection_failure(self, mock_cloudinary):
        """Тест неудачного тестирования соединения"""
        mock_cloudinary.api.root_folders.side_effect = [{"folders": []}, Exception("Connection failed")]
        
        client = CloudinaryClient(self.config)
        assert client.test_connection() is False

class TestImageManager:
    """Тесты для высокоуровневых функций управления изображениями"""
    
    @patch('app.cloudinary_api.image_manager._get_default_client')
    def test_upload_single_image(self, mock_get_client):
        """Тест загрузки одного изображения"""
        mock_client = MagicMock()
        mock_client.upload_image.return_value = {"public_id": "test", "secure_url": "https://test.jpg"}
        mock_get_client.return_value = mock_client
        
        result = upload_single_image("test.jpg", public_id="test")
        assert result["public_id"] == "test"
        mock_client.upload_image.assert_called_once()
    
    @patch('app.cloudinary_api.image_manager._get_default_client')
    def test_get_image_url_with_transformations(self, mock_get_client):
        """Тест получения URL с трансформациями"""
        mock_client = MagicMock()
        mock_client.get_image_url.return_value = "https://cloudinary.com/transformed.jpg"
        mock_get_client.return_value = mock_client
        
        transformations = {"width": 300, "height": 200}
        url = get_image_url_with_transformations("test_id", transformations)
        
        assert url == "https://cloudinary.com/transformed.jpg"
        mock_client.get_image_url.assert_called_with(
            public_id="test_id",
            transformations=transformations,
            secure=True
        )
    
    @patch('app.cloudinary_api.image_manager._get_default_client')
    def test_upload_car_photos(self, mock_get_client):
        """Тест загрузки фотографий автомобиля"""
        mock_client = MagicMock()
        mock_client.upload_image.side_effect = [
            {"public_id": "car_123_1", "secure_url": "https://test1.jpg"},
            {"public_id": "car_123_2", "secure_url": "https://test2.jpg"}
        ]
        mock_get_client.return_value = mock_client
        
        results = upload_car_photos(["photo1.jpg", "photo2.jpg"], "123")
        
        assert len(results) == 2
        assert results[0]["public_id"] == "car_123_1"
        assert results[1]["public_id"] == "car_123_2"
        assert mock_client.upload_image.call_count == 2
    
    @patch('app.cloudinary_api.image_manager._get_default_client')
    def test_get_car_photos_urls(self, mock_get_client):
        """Тест получения URL фотографий автомобиля"""
        mock_client = MagicMock()
        mock_client.get_image_url.side_effect = [
            "https://cloudinary.com/cars/car_123_1.jpg",
            "https://cloudinary.com/cars/car_123_2.jpg",
            Exception("Not found")  # Для остановки поиска
        ]
        mock_get_client.return_value = mock_client
        
        urls = get_car_photos_urls("123", count=5, folder="cars")
        
        assert len(urls) == 2
        assert "car_123_1" in urls[0]
        assert "car_123_2" in urls[1]
    
    @patch('app.cloudinary_api.image_manager._get_default_client')
    def test_create_car_gallery(self, mock_get_client):
        """Тест создания галереи автомобиля"""
        mock_client = MagicMock()
        # Мок для получения оригинальных URL
        mock_client.get_image_url.side_effect = [
            "https://original1.jpg",
            "https://original2.jpg", 
            Exception("Not found"),  # Остановка поиска оригиналов
            "https://large1.jpg",    # Большие версии
            "https://large2.jpg",
            "https://thumb1.jpg",    # Миниатюры
            "https://thumb2.jpg",
            Exception("Not found")   # Остановка поиска миниатюр
        ]
        mock_get_client.return_value = mock_client
        
        gallery = create_car_gallery("123", folder="cars")
        
        assert len(gallery["original"]) == 2
        assert len(gallery["large"]) == 2
        assert len(gallery["thumbnails"]) == 2
        assert gallery["count"] == 2

class TestLegacyWrapper:
    """Тесты для legacy совместимости"""
    
    @patch('app.cloudinary_api.legacy_wrapper._get_legacy_client')
    @patch.dict(os.environ, {'CLOUDINARY_URL': 'cloudinary://test'})
    def test_upload_image_to_cloudinary_success(self, mock_get_client):
        """Тест legacy функции загрузки изображения"""
        mock_client = MagicMock()
        mock_client.upload_image.return_value = {
            "public_id": "test_image",
            "secure_url": "https://cloudinary.com/test_image.jpg"
        }
        mock_get_client.return_value = mock_client
        
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
            tmp_file.write(b"fake image data")
            tmp_path = tmp_file.name
        
        try:
            result = upload_image_to_cloudinary(tmp_path, "test_image")
            assert result["public_id"] == "test_image"
            assert result["secure_url"] == "https://cloudinary.com/test_image.jpg"
        finally:
            os.unlink(tmp_path)
    
    @patch('app.cloudinary_api.legacy_wrapper._get_legacy_client')
    @patch.dict(os.environ, {}, clear=True)  # Очищаем переменные окружения
    def test_upload_image_no_config(self, mock_get_client):
        """Тест legacy функции без конфигурации"""
        mock_get_client.return_value = None
        
        result = upload_image_to_cloudinary("test.jpg")
        assert result is None
    
    @patch('app.cloudinary_api.legacy_wrapper._get_legacy_client')
    @patch.dict(os.environ, {'CLOUDINARY_URL': 'cloudinary://test'})
    def test_get_image_url_from_cloudinary_success(self, mock_get_client):
        """Тест legacy функции получения URL"""
        mock_client = MagicMock()
        mock_client.get_image_url.return_value = "https://cloudinary.com/test.jpg"
        mock_get_client.return_value = mock_client
        
        url = get_image_url_from_cloudinary("test_id")
        assert url == "https://cloudinary.com/test.jpg"
    
    @patch('app.cloudinary_api.legacy_wrapper._get_legacy_client')
    @patch.dict(os.environ, {'CLOUDINARY_URL': 'cloudinary://test'})
    def test_legacy_get_car_photos_urls(self, mock_get_client):
        """Тест legacy функции получения URL фотографий автомобиля"""
        mock_client = MagicMock()
        mock_client.get_image_url.side_effect = [
            "https://cloudinary.com/car_123_1.jpg",
            "https://cloudinary.com/car_123_2.jpg",
            Exception("Not found")
        ]
        mock_get_client.return_value = mock_client
        
        urls = legacy_get_car_photos_urls("123", count=5)
        assert len(urls) == 2
    
    @patch('app.cloudinary_api.legacy_wrapper._get_legacy_client')
    @patch.dict(os.environ, {'CLOUDINARY_URL': 'cloudinary://test'})
    def test_test_cloudinary_connection_success(self, mock_get_client):
        """Тест legacy функции тестирования соединения"""
        mock_client = MagicMock()
        mock_client.test_connection.return_value = True
        mock_get_client.return_value = mock_client
        
        result = test_cloudinary_connection()
        assert result is True
    
    @patch('app.cloudinary_api.legacy_wrapper._get_legacy_client')
    def test_test_cloudinary_connection_no_client(self, mock_get_client):
        """Тест legacy функции тестирования соединения без клиента"""
        mock_get_client.return_value = None
        
        result = test_cloudinary_connection()
        assert result is False

class TestCloudinaryExceptions:
    """Тесты для специализированных исключений"""
    
    def test_cloudinary_client_error(self):
        """Тест базового исключения CloudinaryClientError"""
        with pytest.raises(CloudinaryClientError, match="Test error"):
            raise CloudinaryClientError("Test error")
    
    def test_cloudinary_config_error(self):
        """Тест исключения CloudinaryConfigError"""
        with pytest.raises(CloudinaryConfigError, match="Config error"):
            raise CloudinaryConfigError("Config error")
    
    def test_cloudinary_upload_error(self):
        """Тест исключения CloudinaryUploadError"""
        with pytest.raises(CloudinaryUploadError, match="Upload error"):
            raise CloudinaryUploadError("Upload error")
    
    def test_cloudinary_api_error(self):
        """Тест исключения CloudinaryAPIError"""
        with pytest.raises(CloudinaryAPIError, match="API error"):
            raise CloudinaryAPIError("API error")

# Функции для интеграционных тестов (требуют реальной конфигурации Cloudinary)

@pytest.mark.integration
@pytest.mark.skipif(not os.getenv("CLOUDINARY_URL"), reason="Cloudinary не сконфигурирован")
class TestCloudinaryIntegration:
    """Интеграционные тесты с реальным Cloudinary API"""
    
    def test_real_cloudinary_connection(self):
        """Тест реального соединения с Cloudinary"""
        config = CloudinaryConfig()
        client = CloudinaryClient(config)
        assert client.test_connection() is True
    
    def test_real_cloudinary_stats(self):
        """Тест получения реальной статистики Cloudinary"""
        config = CloudinaryConfig()
        client = CloudinaryClient(config)
        stats = client.get_upload_stats()
        assert isinstance(stats, dict)
        # Cloudinary должен возвращать статистику использования
        assert "credits_used" in stats or len(stats) == 0  # Пустой словарь при ошибке

if __name__ == "__main__":
    # Запуск тестов
    pytest.main([__file__, "-v"]) 