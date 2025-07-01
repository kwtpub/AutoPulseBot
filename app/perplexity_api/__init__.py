"""
Perplexity API Module - изолированный модуль для работы с Perplexity AI

Этот модуль предоставляет:
- Клиент для Perplexity API
- Форматирование объявлений и промптов
- Legacy wrapper для совместимости
- Конфигурацию и настройки
"""

# Публичное API модуля
from .perplexity_client import PerplexityClient, PerplexityConfig
from .text_formatter import (
    format_car_announcement,
    create_car_description_prompt,
    extract_car_info_from_text
)
from .legacy_wrapper import PerplexityProcessor

# Удобные функции для быстрого использования
from .text_formatter import format_car_announcement as format_announcement

__all__ = [
    # Основные классы
    'PerplexityClient',
    'PerplexityConfig', 
    'PerplexityProcessor',  # Legacy совместимость
    
    # Форматирование текста
    'format_car_announcement',
    'create_car_description_prompt',
    'extract_car_info_from_text',
    'format_announcement',  # Короткий псевдоним
]

__version__ = '1.0.0' 