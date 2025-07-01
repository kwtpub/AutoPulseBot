"""
Тестирование OCR API модуля
"""

import os
import sys
import asyncio
from typing import Dict, Any

# Добавляем корневую папку в путь для импортов
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app.ocr_api import (
    OCRClient, 
    OCRConfig, 
    extract_text_from_image,
    extract_caption_from_image,
    process_images_ocr,
    extract_text_legacy
)
from app.ocr_api.legacy_wrapper import OCRProcessor, test_ocr_connection, blip_image_caption


def print_test_result(test_name: str, result: Dict[str, Any], success: bool = True):
    """Вывод результата теста"""
    status = "✅ УСПЕХ" if success else "❌ ОШИБКА"
    print(f"\n{status} - {test_name}")
    print("-" * 50)
    
    if isinstance(result, dict):
        for key, value in result.items():
            print(f"{key}: {value}")
    else:
        print(f"Результат: {result}")
    print("-" * 50)


async def test_health_check():
    """Тест проверки состояния OCR сервисов"""
    print("\n🔍 Тестирование проверки состояния OCR сервисов...")
    
    try:
        status = test_ocr_connection()
        print_test_result("Health Check", status)
        return True
    except Exception as e:
        print_test_result("Health Check", {"error": str(e)}, False)
        return False


async def test_ocr_client():
    """Тест основного OCR клиента"""
    print("\n🔍 Тестирование OCR клиента...")
    
    # Создаем тестовое изображение (простой текст)
    test_image_path = create_test_image()
    
    try:
        # Тест с Tesseract
        config = OCRConfig(use_tesseract=True, use_yandex=False)
        client = OCRClient(config)
        
        text = await client.extract_text(test_image_path)
        print_test_result("OCR Client (Tesseract)", {"text": text, "length": len(text)})
        
        # Очистка
        if os.path.exists(test_image_path):
            os.remove(test_image_path)
        
        return True
        
    except Exception as e:
        print_test_result("OCR Client", {"error": str(e)}, False)
        if os.path.exists(test_image_path):
            os.remove(test_image_path)
        return False


async def test_yandex_ocr():
    """Тест Yandex OCR (если настроен)"""
    print("\n🔍 Тестирование Yandex OCR...")
    
    # Проверяем наличие Yandex токенов
    from dotenv import load_dotenv
    load_dotenv()
    
    yandex_token = os.getenv('YANDEX_IAM_TOKEN')
    yandex_folder = os.getenv('YANDEX_FOLDER_ID')
    
    if not yandex_token or not yandex_folder:
        print_test_result("Yandex OCR", {"status": "Пропущен - нет токенов"})
        return True
    
    test_image_path = create_test_image()
    
    try:
        config = OCRConfig(use_yandex=True)
        client = OCRClient(config)
        
        text = await client.extract_text_yandex(test_image_path)
        print_test_result("Yandex OCR", {"text": text, "length": len(text)})
        
        # Очистка
        if os.path.exists(test_image_path):
            os.remove(test_image_path)
        
        return True
        
    except Exception as e:
        print_test_result("Yandex OCR", {"error": str(e)}, False)
        if os.path.exists(test_image_path):
            os.remove(test_image_path)
        return False


async def test_legacy_compatibility():
    """Тест совместимости со старым интерфейсом"""
    print("\n🔍 Тестирование совместимости со старым кодом...")
    
    test_image_path = create_test_image()
    
    try:
        # Тест старого класса OCRProcessor
        ocr = OCRProcessor(lang='ru', use_yandex=False)
        text = await ocr.extract_text(test_image_path)
        
        print_test_result("Legacy OCRProcessor", {"text": text, "length": len(text)})
        
        # Тест функции extract_text_legacy
        text2 = await extract_text_legacy(test_image_path, use_yandex=False)
        print_test_result("Legacy Function", {"text": text2, "length": len(text2)})
        
        # Очистка
        if os.path.exists(test_image_path):
            os.remove(test_image_path)
        
        return True
        
    except Exception as e:
        print_test_result("Legacy Compatibility", {"error": str(e)}, False)
        if os.path.exists(test_image_path):
            os.remove(test_image_path)
        return False


async def test_high_level_functions():
    """Тест высокоуровневых функций"""
    print("\n🔍 Тестирование высокоуровневых функций...")
    
    test_image_path = create_test_image()
    
    try:
        # Тест extract_text_from_image
        text = await extract_text_from_image(test_image_path, use_yandex=False)
        print_test_result("High-level extract_text_from_image", {"text": text, "length": len(text)})
        
        # Тест process_images_ocr
        texts = await process_images_ocr([test_image_path], use_yandex=False)
        print_test_result("High-level process_images_ocr", {"texts": texts, "count": len(texts)})
        
        # Очистка
        if os.path.exists(test_image_path):
            os.remove(test_image_path)
        
        return True
        
    except Exception as e:
        print_test_result("High-level Functions", {"error": str(e)}, False)
        if os.path.exists(test_image_path):
            os.remove(test_image_path)
        return False


def create_test_image() -> str:
    """Создание простого тестового изображения с текстом"""
    try:
        from PIL import Image, ImageDraw, ImageFont
        
        # Создаем белое изображение
        img = Image.new('RGB', (400, 100), color='white')
        draw = ImageDraw.Draw(img)
        
        # Добавляем простой текст
        text = "Test OCR Text 123"
        try:
            # Пытаемся использовать системный шрифт
            font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 20)
        except:
            # Если нет, используем стандартный
            font = ImageFont.load_default()
        
        draw.text((10, 30), text, fill='black', font=font)
        
        # Сохраняем во временную папку
        temp_dir = "temp"
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
        
        test_path = os.path.join(temp_dir, "test_ocr_image.png")
        img.save(test_path)
        
        return test_path
        
    except ImportError:
        # Если PIL не установлен, создаем фиктивный файл
        temp_dir = "temp"
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
        
        test_path = os.path.join(temp_dir, "test_ocr_dummy.txt")
        with open(test_path, "w") as f:
            f.write("dummy test file")
        
        return test_path


async def main():
    """Основная функция тестирования"""
    print("🚀 Запуск тестирования OCR API модуля")
    print("=" * 60)
    
    tests = [
        test_health_check,
        test_ocr_client,
        test_yandex_ocr,
        test_legacy_compatibility,
        test_high_level_functions
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            result = await test()
            if result:
                passed += 1
        except Exception as e:
            print(f"❌ Ошибка в тесте {test.__name__}: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 Результаты тестирования: {passed}/{total} тестов пройдено")
    
    if passed == total:
        print("🎉 Все тесты пройдены успешно!")
    else:
        print("⚠️ Некоторые тесты не пройдены. Проверьте конфигурацию.")
    
    # Очистка временных файлов
    if os.path.exists("temp"):
        import shutil
        shutil.rmtree("temp", ignore_errors=True)


if __name__ == "__main__":
    asyncio.run(main()) 