#!/usr/bin/env python3
"""
Простой тест команды /getauto без отправки фотографий
"""
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.commands.getauto import get_car_from_api, format_car_message

async def test_getauto():
    """Тестирует получение данных автомобиля"""
    if len(sys.argv) != 2:
        print("Использование: python test_getauto_simple.py <custom_id>")
        sys.exit(1)
    
    custom_id = sys.argv[1]
    
    print(f"🔍 Тестирование получения данных для ID: {custom_id}")
    
    # Получаем данные из API
    car_data = await get_car_from_api(custom_id)
    
    if not car_data:
        print(f"❌ Автомобиль с ID {custom_id} не найден")
        return
    
    print(f"✅ Автомобиль найден: {car_data.get('brand', 'N/A')} {car_data.get('model', 'N/A')}")
    
    # Форматируем сообщение
    message = format_car_message(car_data)
    
    print("\n" + "="*50)
    print("СФОРМИРОВАННОЕ СООБЩЕНИЕ:")
    print("="*50)
    print(message)
    print("="*50)
    
    # Информация о фотографиях
    photos = car_data.get('photos', [])
    if photos:
        print(f"\n📸 Найдено {len(photos)} фотографий:")
        for i, photo_url in enumerate(photos, 1):
            print(f"  {i}. {photo_url}")
    else:
        print("\n📸 Фотографий не найдено")

if __name__ == "__main__":
    asyncio.run(test_getauto()) 