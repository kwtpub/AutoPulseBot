#!/usr/bin/env python3
"""
Тестовый скрипт для проверки интеграции с Cloudinary
"""
import os
import asyncio
from dotenv import load_dotenv
from app.core.cloudinary_uploader import upload_image_to_cloudinary, get_car_photos_urls, get_car_photo_thumbnails

load_dotenv()

async def test_cloudinary():
    """Тестирует загрузку и получение фотографий из Cloudinary"""
    
    # Проверяем настройки
    cloudinary_url = os.getenv("CLOUDINARY_URL")
    if not cloudinary_url:
        print("❌ CLOUDINARY_URL не настроен в .env файле")
        print("Добавьте: CLOUDINARY_URL=cloudinary://api_key:api_secret@cloud_name")
        return
    
    print("✅ Cloudinary URL найден")
    
    # Ищем тестовое изображение
    test_image = None
    for ext in ['jpg', 'jpeg', 'png']:
        for name in ['test', 'example', 'sample']:
            path = f"{name}.{ext}"
            if os.path.exists(path):
                test_image = path
                break
        if test_image:
            break
    
    if not test_image:
        print("⚠️  Тестовое изображение не найдено")
        print("Создайте файл test.jpg для тестирования")
        return
    
    print(f"📸 Найдено тестовое изображение: {test_image}")
    
    # Тестируем загрузку
    custom_id = "test_12345678"
    public_id = f"car_{custom_id}_1"
    
    print(f"🔄 Загружаем изображение в Cloudinary с ID: {public_id}")
    result = upload_image_to_cloudinary(test_image, public_id=public_id)
    
    if result:
        print(f"✅ Загрузка успешна!")
        print(f"📷 URL: {result.get('secure_url')}")
        print(f"🆔 Public ID: {result.get('public_id')}")
        
        # Тестируем получение URL-ов
        print(f"\n🔄 Получаем URL-ы фотографий для автомобиля {custom_id}")
        urls = get_car_photos_urls(custom_id)
        print(f"📷 Найдено {len(urls)} фотографий:")
        for i, url in enumerate(urls, 1):
            print(f"  {i}. {url}")
        
        # Тестируем миниатюры
        print(f"\n🔄 Получаем миниатюры для автомобиля {custom_id}")
        thumbnails = get_car_photo_thumbnails(custom_id, width=150, height=100)
        print(f"🖼️  Найдено {len(thumbnails)} миниатюр:")
        for i, url in enumerate(thumbnails, 1):
            print(f"  {i}. {url}")
            
    else:
        print("❌ Ошибка загрузки в Cloudinary")

if __name__ == "__main__":
    asyncio.run(test_cloudinary()) 