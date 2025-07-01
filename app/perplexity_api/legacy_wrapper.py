"""
Legacy Wrapper - обеспечение совместимости с существующим кодом
Предоставляет старый интерфейс PerplexityProcessor для плавной миграции
"""

import asyncio
from typing import Optional
import logging

from .perplexity_client import PerplexityClient, PerplexityConfig
from .text_formatter import create_car_description_prompt

logger = logging.getLogger(__name__)

class PerplexityProcessor:
    """
    Legacy wrapper для совместимости с существующим кодом
    Эмулирует интерфейс старого PerplexityProcessor
    """
    
    def __init__(self, api_key: str):
        """
        Инициализация с API ключом (совместимость с legacy кодом)
        
        Args:
            api_key: API ключ Perplexity
        """
        self.api_key = api_key
        self.base_url = 'https://api.perplexity.ai'  # Для совместимости
        
        # Создаем конфигурацию с настройками по умолчанию
        self.config = PerplexityConfig(
            api_key=api_key,
            model='sonar-pro',
            temperature=0.2,
            max_tokens=1000,
            timeout=60,
            max_retries=3
        )
        
        # Клиент будет создаваться при первом использовании
        self._client: Optional[PerplexityClient] = None
        
    def _get_client(self) -> PerplexityClient:
        """Получает или создает клиент"""
        if not self._client:
            self._client = PerplexityClient(self.config)
        return self._client
    
    def create_prompt(self, announcement_text: str, ocr_data: str, custom_id: str, markup_percentage: float) -> str:
        """
        Создает промпт для Perplexity (legacy метод)
        
        Args:
            announcement_text: Текст объявления
            ocr_data: OCR данные
            custom_id: Кастомный ID 
            markup_percentage: Процент наценки
            
        Returns:
            Промпт для Perplexity
        """
        return create_car_description_prompt(
            announcement_text=announcement_text,
            ocr_data=ocr_data,
            custom_id=custom_id,
            markup_percentage=markup_percentage
        )
    
    async def process_text(self, prompt: str) -> str:
        """
        Обрабатывает текст через Perplexity API (legacy метод)
        
        Args:
            prompt: Промпт для обработки
            
        Returns:
            Обработанный текст
        """
        client = self._get_client()
        
        try:
            # Системный промпт для лучшего следования инструкциям
            system_prompt = 'Ты — помощник, который точно следует инструкциям по форматированию текста.'
            
            result = await client.process_text(prompt, system_prompt)
            return result
            
        except Exception as e:
            logger.error(f"Error processing text with Perplexity: {e}")
            # Для совместимости с legacy кодом - перебрасываем исключение в старом формате
            raise Exception(f'Perplexity API error: {str(e)}')
    
    async def close(self):
        """Закрытие соединений"""
        if self._client:
            await self._client.close()
            self._client = None

# Дополнительные legacy функции для полной совместимости

async def process_car_announcement(
    announcement_text: str,
    ocr_data: str, 
    custom_id: str,
    markup_percentage: float,
    api_key: str
) -> str:
    """
    Legacy функция для обработки объявления об автомобиле
    
    Args:
        announcement_text: Текст объявления
        ocr_data: OCR данные
        custom_id: Кастомный ID
        markup_percentage: Процент наценки  
        api_key: API ключ
        
    Returns:
        Обработанное объявление
    """
    processor = PerplexityProcessor(api_key)
    
    try:
        prompt = processor.create_prompt(announcement_text, ocr_data, custom_id, markup_percentage)
        result = await processor.process_text(prompt)
        return result
    finally:
        await processor.close()

def test_perplexity_connection(api_key: str) -> bool:
    """
    Legacy функция для тестирования подключения
    
    Args:
        api_key: API ключ для тестирования
        
    Returns:
        True если подключение работает
    """
    async def _test():
        config = PerplexityConfig(api_key=api_key)
        async with PerplexityClient(config) as client:
            return await client.test_connection()
    
    try:
        return asyncio.run(_test())
    except Exception as e:
        logger.error(f"Connection test failed: {e}")
        return False

# Алиасы для совместимости
create_prompt = lambda processor, *args: processor.create_prompt(*args)
process_text = lambda processor, prompt: asyncio.run(processor.process_text(prompt)) 