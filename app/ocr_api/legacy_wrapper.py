"""
Legacy Wrapper - обертки для совместимости с существующим кодом
"""

import os
from typing import List, Optional
from .ocr_client import OCRClient, OCRConfig


# Совместимость с старым классом OCRProcessor
class OCRProcessor:
    """
    Обертка для совместимости со старым интерфейсом OCRProcessor
    """
    
    def __init__(self, lang='ru', use_paddle=False, use_yandex=False):
        self.config = OCRConfig(
            language=lang,
            use_paddle=use_paddle,
            use_yandex=use_yandex,
            use_tesseract=not (use_paddle or use_yandex)
        )
        self.client = OCRClient(self.config)
    
    async def extract_text(self, image_path: str, preprocess=True) -> str:
        """
        Совместимость с старым методом extract_text
        """
        self.config.preprocess_images = preprocess
        return await self.client.extract_text(image_path)
    
    def preprocess_image(self, image_path: str) -> str:
        """
        Совместимость с методом предобработки
        """
        return self.client.preprocess_image(image_path)
    
    async def yandex_ocr(self, image_path: str) -> str:
        """
        Совместимость с методом yandex_ocr
        """
        return await self.client.extract_text_yandex(image_path)


# Глобальная функция для извлечения текста (для text_reader.py)
async def extract_text_from_image(image_path: str, language: str = 'ru') -> str:
    """
    Глобальная функция для извлечения текста из изображения
    Используется в text_reader.py
    
    Args:
        image_path: Путь к изображению
        language: Язык для OCR
        
    Returns:
        Извлеченный текст
    """
    from .text_extractor import extract_text_from_image as extract_func
    return await extract_func(image_path, language=language)


# Функция для обработки списка изображений
async def process_images_ocr(
    image_paths: List[str], 
    language: str = 'ru',
    use_yandex: bool = True
) -> List[str]:
    """
    Обработка списка изображений и извлечение текста
    
    Args:
        image_paths: Список путей к изображениям
        language: Язык для OCR
        use_yandex: Использовать Yandex Vision API
        
    Returns:
        Список извлеченных текстов
    """
    config = OCRConfig(
        language=language,
        use_yandex=use_yandex
    )
    
    client = OCRClient(config)
    results = await client.process_multiple_images(image_paths)
    
    # Возвращаем только тексты для совместимости
    return [result['text'] for result in results]


# Функция для совместимости с announcement_processor.py
async def extract_text_legacy(
    image_path: str,
    lang: str = 'ru',
    use_yandex: bool = True,
    preprocess: bool = True
) -> str:
    """
    Функция для совместимости с существующим кодом
    
    Args:
        image_path: Путь к изображению
        lang: Язык OCR
        use_yandex: Использовать Yandex Vision API
        preprocess: Предобработка изображения
        
    Returns:
        Извлеченный текст
    """
    config = OCRConfig(
        language=lang,
        use_yandex=use_yandex,
        use_tesseract=not use_yandex,
        preprocess_images=preprocess
    )
    
    client = OCRClient(config)
    return await client.extract_text(image_path)


# Функция для генерации описания изображения (совместимость с blip_image_caption)
def blip_image_caption(image_path: str) -> str:
    """
    Синхронная обертка для генерации описания изображения
    Совместимость с существующей функцией blip_image_caption
    
    Args:
        image_path: Путь к изображению
        
    Returns:
        Описание изображения
    """
    import asyncio
    from .text_extractor import extract_caption_from_image
    
    # Запускаем асинхронную функцию синхронно
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Если цикл уже запущен, создаем новый поток
            import threading
            import concurrent.futures
            
            def run_in_thread():
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                try:
                    return new_loop.run_until_complete(extract_caption_from_image(image_path))
                finally:
                    new_loop.close()
            
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(run_in_thread)
                return future.result()
        else:
            return loop.run_until_complete(extract_caption_from_image(image_path))
    except RuntimeError:
        # Если нет активного цикла событий
        return asyncio.run(extract_caption_from_image(image_path))


def test_ocr_connection() -> dict:
    """
    Проверка подключения к OCR сервисам
    
    Returns:
        Статус всех OCR сервисов
    """
    config = OCRConfig(
        use_tesseract=True,
        use_paddle=True,
        use_yandex=True,
        use_blip=True
    )
    
    client = OCRClient(config)
    return client.health_check() 