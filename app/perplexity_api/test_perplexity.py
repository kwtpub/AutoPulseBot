"""
Тесты для Perplexity API модуля
Проверяет функциональность клиента, форматирования и legacy совместимости
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from dataclasses import dataclass

from .perplexity_client import (
    PerplexityClient, 
    PerplexityConfig,
    PerplexityAPIError,
    PerplexityAuthError
)
from .text_formatter import (
    CarInfo,
    extract_car_info_from_text,
    create_car_description_prompt,
    format_car_announcement,
    validate_car_announcement_format
)
from .legacy_wrapper import PerplexityProcessor

class TestPerplexityClient:
    """Тесты для PerplexityClient"""
    
    def setup_method(self):
        """Настройка для каждого теста"""
        self.config = PerplexityConfig(
            api_key="test_key",
            model="sonar-pro",
            timeout=30
        )
        self.client = PerplexityClient(self.config)
    
    async def test_client_initialization(self):
        """Тест инициализации клиента"""
        assert self.client.config.api_key == "test_key"
        assert self.client.config.model == "sonar-pro"
        assert "Bearer test_key" in self.client.headers["Authorization"]
    
    @patch('aiohttp.ClientSession.post')
    async def test_successful_chat_completion(self, mock_post):
        """Тест успешного запроса к API"""
        # Мокаем успешный ответ
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Test response"}}]
        }
        mock_post.return_value.__aenter__.return_value = mock_response
        
        # Создаем клиента с мокнутой сессией
        await self.client._ensure_session()
        
        messages = [{"role": "user", "content": "Test prompt"}]
        result = await self.client.chat_completion(messages)
        
        assert result["choices"][0]["message"]["content"] == "Test response"
    
    @patch('aiohttp.ClientSession.post')
    async def test_auth_error_handling(self, mock_post):
        """Тест обработки ошибки авторизации"""
        mock_response = AsyncMock()
        mock_response.status = 401
        mock_response.text.return_value = "Unauthorized"
        mock_post.return_value.__aenter__.return_value = mock_response
        
        await self.client._ensure_session()
        
        messages = [{"role": "user", "content": "Test"}]
        
        with pytest.raises(PerplexityAuthError):
            await self.client.chat_completion(messages)
    
    async def test_process_text_method(self):
        """Тест упрощенного метода process_text"""
        with patch.object(self.client, 'chat_completion') as mock_completion:
            mock_completion.return_value = {
                "choices": [{"message": {"content": "Processed text"}}]
            }
            
            result = await self.client.process_text("Test prompt")
            assert result == "Processed text"
            
            # Проверяем что был вызван chat_completion с правильными аргументами
            mock_completion.assert_called_once()
            called_messages = mock_completion.call_args[0][0]
            assert len(called_messages) == 1
            assert called_messages[0]["content"] == "Test prompt"
    
    async def test_test_connection(self):
        """Тест метода проверки соединения"""
        with patch.object(self.client, 'chat_completion') as mock_completion:
            mock_completion.return_value = {
                "choices": [{"message": {"content": "OK"}}]
            }
            
            result = await self.client.test_connection()
            assert result is True
    
    async def teardown_method(self):
        """Очистка после каждого теста"""
        await self.client.close()

class TestTextFormatter:
    """Тесты для модуля форматирования текста"""
    
    def test_extract_car_info_basic(self):
        """Тест извлечения базовой информации об автомобиле"""
        text = "Продам Toyota Camry 2015 года, цена 1500000 рублей, пробег 120000 км"
        
        car_info = extract_car_info_from_text(text)
        
        assert car_info.year == 2015
        assert car_info.price == 1500000
        assert car_info.mileage == 120000
    
    def test_extract_car_info_with_engine(self):
        """Тест извлечения информации с объемом двигателя"""
        text = "BMW X5 2018, двигатель 2.0л, автомат, полный привод"
        
        car_info = extract_car_info_from_text(text)
        
        assert car_info.year == 2018
        assert car_info.engine_volume == "2.0"
        assert car_info.transmission == "Автомат"
        assert car_info.drive_type == "Полный"
    
    def test_create_car_description_prompt(self):
        """Тест создания промпта для описания автомобиля"""
        prompt = create_car_description_prompt(
            announcement_text="Toyota Camry 2015",
            ocr_data="дополнительная информация",
            custom_id="test_id",
            markup_percentage=15.0
        )
        
        assert "Toyota Camry 2015" in prompt
        assert "15%" in prompt
        assert "[Марка] [Модель] [Год]" in prompt
        assert "дополнительная информация" in prompt
    
    def test_format_car_announcement(self):
        """Тест форматирования финального объявления"""
        characteristics = {
            "year": "2015",
            "engine": "2.0л",
            "mileage": "120000 км",
            "transmission": "Автомат"
        }
        
        result = format_car_announcement(
            brand="Toyota",
            model="Camry",
            year=2015,
            price=1500000,
            description="Отличное состояние, один владелец",
            characteristics=characteristics
        )
        
        assert "[Toyota] [Camry] [2015]" in result
        assert "1 500 000" in result
        assert "💫 Отличное состояние" in result
        assert "Год: 2015" in result
        assert "#toyota" in result.lower()
    
    def test_validate_car_announcement_format_valid(self):
        """Тест валидации корректного формата"""
        text = "[Toyota] [Camry] [2015] - Цена: 1 500 000 ₽\n\nОписание автомобиля"
        
        is_valid, message = validate_car_announcement_format(text)
        
        assert is_valid is True
        assert "корректен" in message
    
    def test_validate_car_announcement_format_invalid(self):
        """Тест валидации некорректного формата"""
        text = "Toyota Camry 2015 - 1500000 рублей"
        
        is_valid, message = validate_car_announcement_format(text)
        
        assert is_valid is False
        assert "не соответствует формату" in message

class TestLegacyWrapper:
    """Тесты для legacy wrapper"""
    
    def setup_method(self):
        """Настройка для каждого теста"""
        self.processor = PerplexityProcessor("test_api_key")
    
    def test_legacy_processor_initialization(self):
        """Тест инициализации legacy processor"""
        assert self.processor.api_key == "test_api_key"
        assert self.processor.base_url == "https://api.perplexity.ai"
        assert self.processor.config.api_key == "test_api_key"
    
    def test_create_prompt_method(self):
        """Тест создания промпта через legacy интерфейс"""
        prompt = self.processor.create_prompt(
            announcement_text="Test car",
            ocr_data="OCR data",
            custom_id="id123",
            markup_percentage=10.0
        )
        
        assert "Test car" in prompt
        assert "OCR data" in prompt
        assert "10%" in prompt
    
    async def test_process_text_method(self):
        """Тест обработки текста через legacy интерфейс"""
        with patch.object(self.processor, '_get_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.process_text.return_value = "Processed result"
            mock_get_client.return_value = mock_client
            
            result = await self.processor.process_text("Test prompt")
            
            assert result == "Processed result"
            mock_client.process_text.assert_called_once_with(
                "Test prompt", 
                'Ты — помощник, который точно следует инструкциям по форматированию текста.'
            )
    
    async def test_error_handling_compatibility(self):
        """Тест совместимости обработки ошибок"""
        with patch.object(self.processor, '_get_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.process_text.side_effect = Exception("API Error")
            mock_get_client.return_value = mock_client
            
            with pytest.raises(Exception) as exc_info:
                await self.processor.process_text("Test")
            
            assert "Perplexity API error: API Error" in str(exc_info.value)
    
    async def teardown_method(self):
        """Очистка после каждого теста"""
        await self.processor.close()

# Интеграционные тесты (требуют настоящего API ключа)
class TestIntegration:
    """Интеграционные тесты (требуют реального API ключа)"""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_real_api_call(self):
        """
        Тест реального вызова API
        Запускается только с меткой integration и реальным API ключом
        """
        import os
        
        api_key = os.getenv("PERPLEXITY_API_KEY")
        if not api_key:
            pytest.skip("PERPLEXITY_API_KEY not set")
        
        config = PerplexityConfig(api_key=api_key, timeout=30)
        
        async with PerplexityClient(config) as client:
            result = await client.process_text("Say 'Hello, World!'")
            assert "Hello" in result or "hello" in result.lower()

# Pytest конфигурация для запуска тестов
if __name__ == "__main__":
    # Запуск обычных тестов (без интеграционных)
    pytest.main([__file__, "-v", "-m", "not integration"]) 