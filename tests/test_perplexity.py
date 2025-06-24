import pytest
from unittest.mock import patch, AsyncMock
from app.core.perplexity import PerplexityProcessor


class TestPerplexityProcessor:
    """Тесты для PerplexityProcessor."""
    
    def setup_method(self):
        """Настройка перед каждым тестом."""
        self.api_key = "test_api_key"
        self.processor = PerplexityProcessor(self.api_key)
    
    def test_init(self):
        """Тест инициализации процессора."""
        assert self.processor.api_key == self.api_key
        assert self.processor.base_url == 'https://api.perplexity.ai'
        assert 'Authorization' in self.processor.headers
        assert self.processor.headers['Authorization'] == f'Bearer {self.api_key}'
    
    def test_create_prompt(self):
        """Тест создания промпта."""
        announcement_text = "Продается BMW X5 2020 года"
        ocr_data = "Двигатель 3.0, пробег 50000 км"
        custom_id = "12345"
        markup_percentage = 10.0
        
        prompt = self.processor.create_prompt(
            announcement_text, ocr_data, custom_id, markup_percentage
        )
        
        assert isinstance(prompt, str)
        assert announcement_text in prompt
        assert ocr_data in prompt
        assert custom_id in prompt
        assert str(markup_percentage) in prompt
        assert "КРАТКОЕ" in prompt
        assert "максимум 800 символов" in prompt
    
    @pytest.mark.asyncio
    async def test_process_text_success(self):
        """Тест успешной обработки текста."""
        mock_response = {
            'choices': [{'message': {'content': 'Тестовый ответ от AI'}}]
        }
        
        with patch('aiohttp.ClientSession') as mock_session:
            mock_context = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_context
            
            mock_response_obj = AsyncMock()
            mock_response_obj.status = 200
            mock_response_obj.json = AsyncMock(return_value=mock_response)
            mock_context.post.return_value.__aenter__.return_value = mock_response_obj
            
            result = await self.processor.process_text("Тестовый промпт")
            
            assert result == 'Тестовый ответ от AI'
    
    @pytest.mark.asyncio
    async def test_process_text_error(self):
        """Тест обработки ошибки API."""
        with patch('aiohttp.ClientSession') as mock_session:
            mock_context = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_context
            
            mock_response_obj = AsyncMock()
            mock_response_obj.status = 400
            mock_response_obj.text = AsyncMock(return_value="Bad Request")
            mock_context.post.return_value.__aenter__.return_value = mock_response_obj
            
            with pytest.raises(Exception) as exc_info:
                await self.processor.process_text("Тестовый промпт")
            
            assert "Perplexity API error: 400" in str(exc_info.value) 