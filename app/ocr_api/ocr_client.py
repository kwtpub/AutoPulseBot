"""
OCR Client - основной класс для обработки изображений и извлечения текста
"""

import os
import cv2
import base64
import requests
import numpy as np
from PIL import Image
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from dotenv import load_dotenv

try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

try:
    from paddleocr import PaddleOCR
    PADDLE_AVAILABLE = True
except ImportError:
    PADDLE_AVAILABLE = False

try:
    from transformers import BlipProcessor, BlipForConditionalGeneration
    BLIP_AVAILABLE = True
except ImportError:
    BLIP_AVAILABLE = False


@dataclass
class OCRConfig:
    """Конфигурация для OCR клиента"""
    language: str = 'ru'
    use_tesseract: bool = True
    use_paddle: bool = False
    use_yandex: bool = False
    use_blip: bool = False
    preprocess_images: bool = True
    yandex_iam_token: Optional[str] = None
    yandex_folder_id: Optional[str] = None


class OCRClient:
    """
    Универсальный клиент для обработки изображений и извлечения текста
    """
    
    def __init__(self, config: Optional[OCRConfig] = None):
        self.config = config or OCRConfig()
        self._paddle_ocr = None
        self._blip_processor = None
        self._blip_model = None
        
        # Загружаем переменные окружения
        load_dotenv()
        
        # Настройка Yandex API
        if self.config.use_yandex:
            self.config.yandex_iam_token = (
                self.config.yandex_iam_token or 
                os.getenv('YANDEX_IAM_TOKEN')
            )
            self.config.yandex_folder_id = (
                self.config.yandex_folder_id or 
                os.getenv('YANDEX_FOLDER_ID')
            )
    
    @property
    def paddle_ocr(self):
        """Ленивая инициализация PaddleOCR"""
        if self._paddle_ocr is None and PADDLE_AVAILABLE:
            self._paddle_ocr = PaddleOCR(
                use_angle_cls=True, 
                lang=self.config.language
            )
        return self._paddle_ocr
    
    @property
    def blip_processor(self):
        """Ленивая инициализация BLIP processor"""
        if self._blip_processor is None and BLIP_AVAILABLE:
            self._blip_processor = BlipProcessor.from_pretrained(
                "Salesforce/blip-image-captioning-large"
            )
        return self._blip_processor
    
    @property
    def blip_model(self):
        """Ленивая инициализация BLIP model"""
        if self._blip_model is None and BLIP_AVAILABLE:
            self._blip_model = BlipForConditionalGeneration.from_pretrained(
                "Salesforce/blip-image-captioning-large"
            )
        return self._blip_model
    
    def preprocess_image(self, image_path: str) -> str:
        """
        Предварительная обработка изображения для улучшения OCR
        
        Args:
            image_path: Путь к изображению
            
        Returns:
            Путь к обработанному изображению
        """
        try:
            # Загрузка изображения
            img = cv2.imread(image_path)
            if img is None:
                raise FileNotFoundError(f"Не удалось открыть изображение: {image_path}")
            
            # Перевод в градации серого
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Бинаризация
            _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # Удаление шума
            denoised = cv2.fastNlMeansDenoising(thresh)
            
            # Сохранение обработанного изображения
            processed_path = image_path.replace('.', '_processed.')
            cv2.imwrite(processed_path, denoised)
            
            return processed_path
            
        except Exception as e:
            raise Exception(f"Ошибка предобработки изображения: {str(e)}")
    
    async def extract_text_tesseract(self, image_path: str) -> str:
        """
        Извлечение текста с помощью Tesseract OCR
        
        Args:
            image_path: Путь к изображению
            
        Returns:
            Извлеченный текст
        """
        if not TESSERACT_AVAILABLE:
            raise ImportError("Tesseract не установлен")
        
        try:
            processed_path = image_path
            if self.config.preprocess_images:
                processed_path = self.preprocess_image(image_path)
            
            # Извлечение текста
            text = pytesseract.image_to_string(
                Image.open(processed_path),
                lang=self.config.language,
                config='--psm 3 --oem 3'
            )
            
            # Очистка результата
            text = ' '.join(text.split())
            
            # Удаляем временный файл если был создан
            if processed_path != image_path and os.path.exists(processed_path):
                os.remove(processed_path)
            
            return text
            
        except Exception as e:
            raise Exception(f"Ошибка Tesseract OCR: {str(e)}")
    
    async def extract_text_paddle(self, image_path: str) -> str:
        """
        Извлечение текста с помощью PaddleOCR
        
        Args:
            image_path: Путь к изображению
            
        Returns:
            Извлеченный текст
        """
        if not PADDLE_AVAILABLE:
            raise ImportError("PaddleOCR не установлен")
        
        try:
            result = self.paddle_ocr.ocr(image_path, cls=True)
            if result and result[0]:
                text = ' '.join([line[1][0] for line in result[0] if line[1]])
                return text
            return ""
            
        except Exception as e:
            raise Exception(f"Ошибка PaddleOCR: {str(e)}")
    
    async def extract_text_yandex(self, image_path: str) -> str:
        """
        Извлечение текста с помощью Yandex Vision API
        
        Args:
            image_path: Путь к изображению
            
        Returns:
            Извлеченный текст
        """
        if not self.config.yandex_iam_token or not self.config.yandex_folder_id:
            raise ValueError("Не настроены Yandex API токены")
        
        try:
            # Кодирование изображения в base64
            with open(image_path, "rb") as f:
                img_data = f.read()
            img_b64 = base64.b64encode(img_data).decode("utf-8")
            
            # Подготовка запроса
            url = "https://vision.api.cloud.yandex.net/vision/v1/batchAnalyze"
            headers = {"Authorization": f"Bearer {self.config.yandex_iam_token}"}
            body = {
                "folderId": self.config.yandex_folder_id,
                "analyze_specs": [{
                    "content": img_b64,
                    "features": [{
                        "type": "TEXT_DETECTION",
                        "text_detection_config": {
                            "language_codes": [self.config.language if self.config.language else '*']
                        }
                    }]
                }]
            }
            
            # Отправка запроса
            response = requests.post(url, json=body, headers=headers)
            response.raise_for_status()
            
            # Обработка ответа
            result = response.json()
            text_blocks = result.get('results', [{}])[0].get('results', [{}])[0].get(
                'textDetection', {}
            ).get('pages', [{}])[0].get('blocks', [])
            
            if not text_blocks:
                return ""
            
            lines = []
            for block in text_blocks:
                for line in block.get('lines', []):
                    line_text = ''.join([word.get('text', '') for word in line.get('words', [])])
                    if line_text:
                        lines.append(line_text)
            
            return '\n'.join(lines)
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                # Попытка обновить токен через yandex_auth модуль
                try:
                    from app.core.yandex_auth import check_and_refresh_iam_token
                    await check_and_refresh_iam_token()
                    # Обновляем токен и повторяем запрос
                    self.config.yandex_iam_token = os.getenv('YANDEX_IAM_TOKEN')
                    return await self.extract_text_yandex(image_path)
                except Exception:
                    raise Exception("Ошибка аутентификации Yandex API")
            else:
                raise Exception(f"Ошибка Yandex Vision API: {e}")
        except Exception as e:
            # Возвращаем пустую строку вместо ошибки для совместимости
            return ""
    
    async def generate_image_caption(self, image_path: str) -> str:
        """
        Генерация описания изображения с помощью BLIP
        
        Args:
            image_path: Путь к изображению
            
        Returns:
            Описание изображения
        """
        if not BLIP_AVAILABLE:
            raise ImportError("BLIP модель не установлена")
        
        try:
            raw_image = Image.open(image_path).convert('RGB')
            
            # Генерация описания
            inputs = self.blip_processor(raw_image, return_tensors="pt")
            out = self.blip_model.generate(**inputs)
            caption = self.blip_processor.decode(out[0], skip_special_tokens=True)
            
            return caption
            
        except Exception as e:
            raise Exception(f"Ошибка генерации описания: {str(e)}")
    
    async def extract_text(self, image_path: str) -> str:
        """
        Универсальный метод извлечения текста
        Использует настроенный в конфигурации метод OCR
        
        Args:
            image_path: Путь к изображению
            
        Returns:
            Извлеченный текст
        """
        if self.config.use_yandex:
            return await self.extract_text_yandex(image_path)
        elif self.config.use_paddle:
            return await self.extract_text_paddle(image_path)
        elif self.config.use_tesseract:
            return await self.extract_text_tesseract(image_path)
        else:
            raise ValueError("Не выбран метод OCR в конфигурации")
    
    async def process_multiple_images(self, image_paths: List[str]) -> List[Dict[str, Any]]:
        """
        Обработка нескольких изображений
        
        Args:
            image_paths: Список путей к изображениям
            
        Returns:
            Список результатов обработки
        """
        results = []
        
        for image_path in image_paths:
            try:
                result = {
                    'image_path': image_path,
                    'text': await self.extract_text(image_path),
                    'success': True,
                    'error': None
                }
                
                # Добавляем описание если включено
                if self.config.use_blip:
                    try:
                        result['caption'] = await self.generate_image_caption(image_path)
                    except Exception as e:
                        result['caption'] = ""
                        result['caption_error'] = str(e)
                
            except Exception as e:
                result = {
                    'image_path': image_path,
                    'text': "",
                    'success': False,
                    'error': str(e)
                }
            
            results.append(result)
        
        return results
    
    def health_check(self) -> Dict[str, Any]:
        """
        Проверка состояния всех OCR сервисов
        
        Returns:
            Статус всех доступных сервисов
        """
        status = {
            'tesseract': TESSERACT_AVAILABLE and self.config.use_tesseract,
            'paddle': PADDLE_AVAILABLE and self.config.use_paddle,
            'yandex': bool(
                self.config.use_yandex and 
                self.config.yandex_iam_token and 
                self.config.yandex_folder_id
            ),
            'blip': BLIP_AVAILABLE and self.config.use_blip,
            'config': {
                'language': self.config.language,
                'preprocess_images': self.config.preprocess_images
            }
        }
        
        return status


# Глобальный клиент для упрощения использования
_default_client = None

def get_client(config: Optional[OCRConfig] = None) -> OCRClient:
    """
    Получить глобальный экземпляр OCR клиента
    
    Args:
        config: Конфигурация (опционально)
        
    Returns:
        Экземпляр OCRClient
    """
    global _default_client
    if _default_client is None or config is not None:
        _default_client = OCRClient(config)
    return _default_client 