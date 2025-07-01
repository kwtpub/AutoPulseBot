"""
Text Extractor - высокоуровневые функции для извлечения текста из изображений
"""

from typing import List, Optional
from .ocr_client import OCRClient, OCRConfig, get_client


async def extract_text_from_image(
    image_path: str, 
    language: str = 'ru',
    use_yandex: bool = True,
    use_paddle: bool = False,
    use_tesseract: bool = False,
    preprocess: bool = True
) -> str:
    """
    Извлечь текст из одного изображения
    
    Args:
        image_path: Путь к изображению
        language: Язык для OCR ('ru', 'en')
        use_yandex: Использовать Yandex Vision API
        use_paddle: Использовать PaddleOCR
        use_tesseract: Использовать Tesseract
        preprocess: Предобработка изображения
        
    Returns:
        Извлеченный текст
    """
    config = OCRConfig(
        language=language,
        use_yandex=use_yandex,
        use_paddle=use_paddle,
        use_tesseract=use_tesseract,
        preprocess_images=preprocess
    )
    
    client = OCRClient(config)
    return await client.extract_text(image_path)


async def extract_text_from_images(
    image_paths: List[str],
    language: str = 'ru',
    use_yandex: bool = True,
    combine_text: bool = True
) -> str:
    """
    Извлечь текст из нескольких изображений
    
    Args:
        image_paths: Список путей к изображениям
        language: Язык для OCR
        use_yandex: Использовать Yandex Vision API
        combine_text: Объединить текст из всех изображений
        
    Returns:
        Извлеченный текст (объединенный или список)
    """
    config = OCRConfig(
        language=language,
        use_yandex=use_yandex
    )
    
    client = OCRClient(config)
    results = await client.process_multiple_images(image_paths)
    
    if combine_text:
        # Объединяем весь найденный текст
        texts = [result['text'] for result in results if result['success'] and result['text']]
        return '\n'.join(texts)
    else:
        # Возвращаем результаты для каждого изображения
        return results


async def extract_caption_from_image(image_path: str) -> str:
    """
    Сгенерировать описание изображения с помощью BLIP
    
    Args:
        image_path: Путь к изображению
        
    Returns:
        Описание изображения
    """
    config = OCRConfig(use_blip=True)
    client = OCRClient(config)
    return await client.generate_image_caption(image_path)


async def extract_text_and_caption(
    image_path: str,
    language: str = 'ru',
    use_yandex: bool = True
) -> dict:
    """
    Извлечь и текст, и описание из изображения
    
    Args:
        image_path: Путь к изображению
        language: Язык для OCR
        use_yandex: Использовать Yandex Vision API
        
    Returns:
        Словарь с текстом и описанием
    """
    config = OCRConfig(
        language=language,
        use_yandex=use_yandex,
        use_blip=True
    )
    
    client = OCRClient(config)
    
    try:
        text = await client.extract_text(image_path)
    except Exception as e:
        text = ""
    
    try:
        caption = await client.generate_image_caption(image_path)
    except Exception as e:
        caption = ""
    
    return {
        'text': text,
        'caption': caption,
        'image_path': image_path
    } 