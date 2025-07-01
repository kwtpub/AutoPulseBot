"""
Генератор уникальных ID для автомобилей
Формат: XXX-XXX (например, 023-455)
"""

import random
import string
from typing import Set
import re

class CustomIDGenerator:
    """Генератор custom ID в формате XXX-XXX"""
    
    def __init__(self):
        self._used_ids: Set[str] = set()
    
    def generate_id(self) -> str:
        """
        Генерирует уникальный ID в формате XXX-XXX
        
        Returns:
            Строка в формате XXX-XXX, например "023-455"
        """
        while True:
            # Генерируем 6 цифр
            digits = [str(random.randint(0, 9)) for _ in range(6)]
            
            # Форматируем как XXX-XXX
            custom_id = f"{digits[0]}{digits[1]}{digits[2]}-{digits[3]}{digits[4]}{digits[5]}"
            
            # Проверяем уникальность
            if custom_id not in self._used_ids:
                self._used_ids.add(custom_id)
                return custom_id
    
    def is_valid_format(self, custom_id: str) -> bool:
        """
        Проверяет, соответствует ли ID формату XXX-XXX
        
        Args:
            custom_id: ID для проверки
            
        Returns:
            True если формат правильный, False в противном случае
        """
        if not isinstance(custom_id, str):
            return False
            
        # Проверяем паттерн: 3 цифры, тире, 3 цифры
        pattern = r'^\d{3}-\d{3}$'
        return bool(re.match(pattern, custom_id))
    
    def mark_as_used(self, custom_id: str) -> None:
        """
        Отмечает ID как уже использованный
        
        Args:
            custom_id: ID для отметки
        """
        if self.is_valid_format(custom_id):
            self._used_ids.add(custom_id)
    
    def reset_used_ids(self) -> None:
        """Очищает список использованных ID"""
        self._used_ids.clear()
    
    def get_used_ids_count(self) -> int:
        """Возвращает количество использованных ID"""
        return len(self._used_ids)

# Глобальный экземпляр генератора
_global_generator = CustomIDGenerator()

def generate_custom_id() -> str:
    """
    Удобная функция для генерации custom ID
    
    Returns:
        Уникальный ID в формате XXX-XXX
    """
    return _global_generator.generate_id()

def is_valid_custom_id(custom_id: str) -> bool:
    """
    Проверяет валидность формата custom ID
    
    Args:
        custom_id: ID для проверки
        
    Returns:
        True если формат правильный
    """
    return _global_generator.is_valid_format(custom_id)

def mark_id_as_used(custom_id: str) -> None:
    """
    Отмечает ID как использованный
    
    Args:
        custom_id: ID для отметки
    """
    _global_generator.mark_as_used(custom_id)

def convert_old_id_to_new_format(old_id: str) -> str:
    """
    Конвертирует старый формат ID в новый
    Для совместимости с существующими данными
    
    Args:
        old_id: Старый ID (например, "12345678")
        
    Returns:
        Новый ID в формате XXX-XXX
    """
    # Если уже в новом формате, возвращаем как есть
    if is_valid_custom_id(old_id):
        return old_id
    
    # Если старый формат - берем последние 6 цифр
    digits_only = ''.join(filter(str.isdigit, str(old_id)))
    
    if len(digits_only) >= 6:
        # Берем последние 6 цифр
        last_six = digits_only[-6:]
        return f"{last_six[:3]}-{last_six[3:]}"
    else:
        # Если цифр меньше 6, дополняем нулями и генерируем новый
        return generate_custom_id()

def extract_custom_id_from_text(text: str) -> str:
    """
    Извлекает custom ID из текста (для парсинга сообщений)
    
    Args:
        text: Текст для поиска ID
        
    Returns:
        Найденный ID в формате XXX-XXX или пустая строка если не найден
    """
    if not text:
        return ""
    
    # Ищем паттерн XXX-XXX в тексте
    pattern = r'\b\d{3}-\d{3}\b'
    match = re.search(pattern, text)
    
    if match:
        return match.group()
    
    return ""

# Дополнительные утилиты для работы с ID

def format_id_for_display(custom_id: str) -> str:
    """
    Форматирует ID для красивого отображения
    
    Args:
        custom_id: ID для форматирования
        
    Returns:
        Отформатированный ID
    """
    if is_valid_custom_id(custom_id):
        return f"🆔 {custom_id}"
    else:
        return f"🆔 {custom_id} (неверный формат)"

def generate_batch_ids(count: int) -> list[str]:
    """
    Генерирует несколько уникальных ID
    
    Args:
        count: Количество ID для генерации
        
    Returns:
        Список уникальных ID
    """
    return [generate_custom_id() for _ in range(count)]

def get_id_statistics() -> dict:
    """
    Возвращает статистику по использованным ID
    
    Returns:
        Словарь со статистикой
    """
    total_possible = 1000000  # 000-000 до 999-999
    used_count = _global_generator.get_used_ids_count()
    
    return {
        "total_possible": total_possible,
        "used_count": used_count,
        "remaining": total_possible - used_count,
        "usage_percentage": (used_count / total_possible) * 100
    }

# Функции для тестирования

def test_id_generation():
    """Тестирует генерацию ID"""
    print("=== Тестирование генерации Custom ID ===")
    
    # Генерируем несколько ID
    ids = generate_batch_ids(10)
    print(f"Сгенерированы ID: {ids}")
    
    # Проверяем валидность
    for custom_id in ids:
        is_valid = is_valid_custom_id(custom_id)
        print(f"{custom_id}: {'✅ валидный' if is_valid else '❌ невалидный'}")
    
    # Проверяем уникальность
    unique_ids = set(ids)
    print(f"Уникальных из {len(ids)}: {len(unique_ids)}")
    
    # Статистика
    stats = get_id_statistics()
    print(f"Статистика: использовано {stats['used_count']} из {stats['total_possible']} возможных")
    
    # Тест конвертации старых ID
    old_ids = ["12345678", "ABC123456", "999", "test-id"]
    print("\nТест конвертации старых ID:")
    for old_id in old_ids:
        new_id = convert_old_id_to_new_format(old_id)
        print(f"{old_id} → {new_id}")
    
    # Тест извлечения из текста
    test_texts = [
        "ID: 123-456",
        "Автомобиль 789-012 доступен",
        "Код объявления: 555-777, звоните!",
        "Никаких ID в этом тексте"
    ]
    print("\nТест извлечения ID из текста:")
    for text in test_texts:
        extracted_id = extract_custom_id_from_text(text)
        print(f"'{text}' → {'✅ ' + extracted_id if extracted_id else '❌ не найден'}")

if __name__ == "__main__":
    test_id_generation() 