"""
Perplexity API Client - основной клиент для работы с Perplexity AI
Поддерживает различные модели, конфигурацию и обработку ошибок
"""

import aiohttp
import json
import asyncio
from dataclasses import dataclass
from typing import Dict, Optional, List, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

@dataclass
class PerplexityConfig:
    """Конфигурация для Perplexity API клиента"""
    api_key: str
    model: str = 'sonar-pro'
    base_url: str = 'https://api.perplexity.ai'
    temperature: float = 0.2
    max_tokens: int = 1000
    timeout: int = 60
    max_retries: int = 3
    retry_delay: float = 1.0

class PerplexityClient:
    """
    Современный клиент для Perplexity API с улучшенной обработкой ошибок
    и гибкой конфигурацией
    """
    
    def __init__(self, config: PerplexityConfig):
        self.config = config
        self.headers = {
            'Authorization': f'Bearer {config.api_key}',
            'Content-Type': 'application/json',
            'User-Agent': 'TelegramAutoPostBot/1.0'
        }
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.config.timeout)
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
            
    async def _ensure_session(self):
        """Создает сессию если она не существует"""
        if not self.session:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.config.timeout)
            )
    
    async def close(self):
        """Закрытие сессии"""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Выполняет chat completion запрос к Perplexity API
        
        Args:
            messages: Список сообщений в формате [{"role": "user", "content": "..."}]
            model: Переопределить модель из конфигурации
            temperature: Переопределить температуру
            max_tokens: Переопределить максимальное количество токенов
            
        Returns:
            Полный ответ от API
        """
        await self._ensure_session()
        
        payload = {
            'model': model or self.config.model,
            'messages': messages,
            'temperature': temperature or self.config.temperature,
            'max_tokens': max_tokens or self.config.max_tokens
        }
        
        for attempt in range(self.config.max_retries):
            try:
                logger.debug(f"Perplexity API request (attempt {attempt + 1}): {payload['model']}")
                
                async with self.session.post(
                    f'{self.config.base_url}/chat/completions',
                    headers=self.headers,
                    json=payload
                ) as response:
                    
                    if response.status == 200:
                        result = await response.json()
                        logger.debug("Perplexity API response received successfully")
                        return result
                    
                    # Обработка различных ошибок
                    error_text = await response.text()
                    
                    if response.status == 401:
                        raise PerplexityAuthError("Неверный API ключ Perplexity")
                    elif response.status == 429:
                        # Rate limit - ждем дольше
                        if attempt < self.config.max_retries - 1:
                            wait_time = self.config.retry_delay * (2 ** attempt)
                            logger.warning(f"Rate limit hit, waiting {wait_time}s")
                            await asyncio.sleep(wait_time)
                            continue
                        raise PerplexityRateLimitError("Превышен лимит запросов Perplexity")
                    elif response.status >= 500:
                        # Серверная ошибка - повторяем
                        if attempt < self.config.max_retries - 1:
                            wait_time = self.config.retry_delay * (attempt + 1)
                            logger.warning(f"Server error {response.status}, retrying in {wait_time}s")
                            await asyncio.sleep(wait_time)
                            continue
                        raise PerplexityServerError(f"Ошибка сервера Perplexity: {response.status}")
                    else:
                        raise PerplexityAPIError(f"Perplexity API error: {response.status} {error_text}")
                        
            except aiohttp.ClientError as e:
                if attempt < self.config.max_retries - 1:
                    wait_time = self.config.retry_delay * (attempt + 1)
                    logger.warning(f"Network error, retrying in {wait_time}s: {e}")
                    await asyncio.sleep(wait_time)
                    continue
                raise PerplexityNetworkError(f"Ошибка сети при обращении к Perplexity: {e}")
        
        raise PerplexityAPIError("Превышено максимальное количество попыток")
    
    async def process_text(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        Упрощенный метод для обработки текста
        
        Args:
            prompt: Основной промпт
            system_prompt: Системный промпт (опционально)
            
        Returns:
            Обработанный текст
        """
        messages = []
        
        if system_prompt:
            messages.append({'role': 'system', 'content': system_prompt})
            
        messages.append({'role': 'user', 'content': prompt})
        
        result = await self.chat_completion(messages)
        return result['choices'][0]['message']['content']
    
    async def test_connection(self) -> bool:
        """
        Тестирует подключение к Perplexity API
        
        Returns:
            True если подключение работает
        """
        try:
            test_messages = [
                {'role': 'user', 'content': 'Test connection. Reply with "OK"'}
            ]
            
            result = await self.chat_completion(test_messages)
            response_text = result['choices'][0]['message']['content'].strip().lower()
            
            return 'ok' in response_text or 'успешно' in response_text
            
        except Exception as e:
            logger.error(f"Perplexity connection test failed: {e}")
            return False


# Кастомные исключения для различных типов ошибок
class PerplexityError(Exception):
    """Базовый класс для ошибок Perplexity API"""
    pass

class PerplexityAPIError(PerplexityError):
    """Общая ошибка API"""
    pass

class PerplexityAuthError(PerplexityError):
    """Ошибка авторизации"""
    pass

class PerplexityRateLimitError(PerplexityError):
    """Превышен лимит запросов"""
    pass

class PerplexityServerError(PerplexityError):
    """Серверная ошибка"""
    pass

class PerplexityNetworkError(PerplexityError):
    """Ошибка сети"""
    pass 