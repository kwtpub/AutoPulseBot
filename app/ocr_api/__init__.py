"""
OCR API Module

Изолированный модуль для обработки изображений и извлечения текста.
Поддерживает Tesseract, PaddleOCR, Yandex Vision API и BLIP caption.
"""

from .ocr_client import OCRClient, OCRConfig
from .text_extractor import extract_text_from_image, extract_caption_from_image
from .legacy_wrapper import process_images_ocr, extract_text_legacy

__all__ = [
    'OCRClient',
    'OCRConfig', 
    'extract_text_from_image',
    'extract_caption_from_image',
    'process_images_ocr',
    'extract_text_legacy'
] 