#!/usr/bin/env python3
"""
Тестовый скрипт для проверки работы изолированного Storage API
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.storage_api.database_client import get_client, check_car_duplicate
from app.storage_api.legacy_wrapper import send_car_to_node, check_duplicate_car, test_database_connection

def test_health_check():
    """Тест проверки здоровья API"""
    print("🏥 Тестирование health check...")
    
    client = get_client()
    is_healthy = client.health_check()
    
    if is_healthy:
        print("✅ API работает!")
        return True
    else:
        print("❌ API недоступен!")
        return False

def test_duplicate_check():
    """Тест проверки дубликатов"""
    print("\n🔍 Тестирование проверки дубликатов...")
    
    # Проверяем несуществующий дубликат
    result = check_car_duplicate(99999, "@test_channel")
    
    if result is None:
        print("✅ Дубликат не найден (ожидаемо)")
    else:
        print(f"⚠️ Неожиданно найден дубликат: {result}")

def test_save_car():
    """Тест сохранения автомобиля"""
    print("\n💾 Тестирование сохранения автомобиля...")
    
    test_car_data = {
        'custom_id': f'test-{os.getpid()}',  # Уникальный ID
        'source_message_id': 12345,
        'source_channel_name': '@test_channel',
        'brand': 'Test',
        'model': 'Car',
        'year': 2023,
        'price': 10000.0,
        'description': 'Тестовый автомобиль для проверки Storage API',
        'photos': ['https://example.com/test.jpg'],
        'status': 'available'
    }
    
    # Тестируем через прямой вызов клиента
    client = get_client()
    from app.storage_api.database_client import CarData
    
    car_data = CarData(
        custom_id=test_car_data['custom_id'],
        source_message_id=test_car_data['source_message_id'],
        source_channel_name=test_car_data['source_channel_name'],
        brand=test_car_data['brand'],
        model=test_car_data['model'],
        year=test_car_data['year'],
        price=test_car_data['price'],
        description=test_car_data['description'],
        photos=test_car_data['photos'],
        status=test_car_data['status']
    )
    
    result = client.save_car(car_data)
    
    if result:
        print("✅ Автомобиль сохранен через прямой API!")
    else:
        print("❌ Ошибка сохранения через прямой API!")
    
    # Тестируем через legacy wrapper
    legacy_result = send_car_to_node(test_car_data)
    
    if 'message' in legacy_result and 'success' in legacy_result['message']:
        print("✅ Автомобиль сохранен через legacy wrapper!")
    else:
        print(f"⚠️ Legacy wrapper результат: {legacy_result}")

def test_get_car():
    """Тест получения автомобиля"""
    print("\n🚗 Тестирование получения автомобиля...")
    
    client = get_client()
    cars = client.get_all_cars(limit=1)
    
    if cars and 'cars' in cars and len(cars['cars']) > 0:
        car = cars['cars'][0]
        custom_id = car['custom_id']
        print(f"✅ Найден автомобиль: {custom_id}")
        
        # Получаем конкретный автомобиль
        specific_car = client.get_car(custom_id)
        if specific_car:
            print(f"✅ Получен автомобиль: {specific_car['brand']} {specific_car['model']}")
        else:
            print("❌ Не удалось получить конкретный автомобиль")
    else:
        print("⚠️ Нет автомобилей в базе для тестирования")

def main():
    """Основная функция тестирования"""
    print("🧪 Запуск тестов Storage API\n")
    
    # 1. Проверка подключения
    if not test_database_connection():
        print("❌ База данных недоступна! Завершение тестов.")
        return False
    
    # 2. Health check
    if not test_health_check():
        print("❌ API недоступен! Завершение тестов.")
        return False
    
    # 3. Тест дубликатов
    test_duplicate_check()
    
    # 4. Тест сохранения
    test_save_car()
    
    # 5. Тест получения
    test_get_car()
    
    print("\n🎉 Все тесты завершены!")
    return True

if __name__ == "__main__":
    main() 