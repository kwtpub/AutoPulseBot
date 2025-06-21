import pytesseract
from PIL import Image
import cv2
import numpy as np
from paddleocr import PaddleOCR
from transformers import BlipProcessor, BlipForConditionalGeneration
import requests
import base64
from dotenv import load_dotenv

class OCRProcessor:
    def __init__(self, lang='en', use_paddle=False, use_yandex=False):
        self.lang = lang
        self.use_paddle = use_paddle
        self.use_yandex = use_yandex
        if use_paddle:
            # PaddleOCR: 'ru' для русского, 'en' для английского
            self.paddle_ocr = PaddleOCR(use_angle_cls=True, lang=lang)
        else:
            self.paddle_ocr = None
        if use_yandex:
            load_dotenv()
            import os
            self.yandex_token = os.getenv('YANDEX_IAM_TOKEN')
            self.yandex_folder_id = os.getenv('YANDEX_FOLDER_ID')
        
    def yandex_ocr(self, image_path):
        with open(image_path, "rb") as f:
            img_data = f.read()
        img_b64 = base64.b64encode(img_data).decode("utf-8")
        url = "https://vision.api.cloud.yandex.net/vision/v1/batchAnalyze"
        headers = {"Authorization": f"Bearer {self.yandex_token}"}
        body = {
            "folderId": self.yandex_folder_id,
            "analyze_specs": [{
                "content": img_b64,
                "features": [{
                    "type": "TEXT_DETECTION",
                    "text_detection_config": {
                        "language_codes": [self.lang if self.lang else '*']
                    }
                }]
            }]
        }
        response = requests.post(url, json=body, headers=headers)
        response.raise_for_status()
        result = response.json()
        try:
            text_blocks = result['results'][0]['results'][0]['textDetection']['pages'][0].get('blocks', [])
            if not text_blocks:
                # Нет текста на фото — не ошибка, возвращаем пустую строку
                return ''
            lines = []
            for block in text_blocks:
                for line in block['lines']:
                    lines.append(''.join([word['text'] for word in line['words']]))
            return '\n'.join(lines)
        except Exception as e:
            # Если структура ответа неожиданная, но blocks отсутствует — тоже не ошибка
            return ''

    def preprocess_image(self, image_path):
        # Загрузка изображения
        img = cv2.imread(image_path)
        if img is None:
            raise FileNotFoundError(f"Файл не найден или не удалось открыть: {image_path}")
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
        
    def extract_text(self, image_path, preprocess=True):
        if self.use_yandex:
            return self.yandex_ocr(image_path)
        if self.use_paddle:
            # PaddleOCR не требует препроцессинга
            result = self.paddle_ocr.ocr(image_path, cls=True)
            text = ' '.join([line[1][0] for line in result[0]])
            return text
        try:
            if preprocess:
                image_path = self.preprocess_image(image_path)
            # Извлечение текста через Tesseract
            text = pytesseract.image_to_string(
                Image.open(image_path),
                lang=self.lang,
                config='--psm 3 --oem 3'
            )
            # Очистка результата
            text = ' '.join(text.split())
            return text
        except Exception as e:
            raise Exception(f'OCR failed: {str(e)}')

def blip_image_caption(image_path):
    processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-large")
    model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-large")

    raw_image = Image.open(image_path).convert('RGB')

    # Безусловное описание (универсальное)
    inputs = processor(raw_image, return_tensors="pt")
    out = model.generate(**inputs)
    caption = processor.decode(out[0], skip_special_tokens=True)
    return caption