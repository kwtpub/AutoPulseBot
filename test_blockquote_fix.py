#!/usr/bin/env python3
"""
Тест для проверки исправления blockquote форматирования
"""

from app.utils.announcement_processor import format_perplexity_response_with_quotes

# Пример ответа с проблемной секцией
test_response = """<b>Mercedes-Benz CLS 300 2022</b> — премиальный седан с отличными характеристиками.

🛠 <b>Технические характеристики:</b>
Двигатель: 2.0T 258HP
Привод: задний
Коробка: автомат
Пробег: 40 000 км

📊 <b>Дополнительные детали:</b>
⚙️ Электронная система стабилизации ESP
⚙️ Антиблокировочная система ABS
⚙️ Система помощи при парковке
⚙️ Круиз-контроль адаптивный

🛡 <b>Состояние и документы:</b>
Состояние: отличное
Документы: в порядке

Custom ID: 020-432
#Mercedes #CLS #2022"""

print("=== ИСХОДНЫЙ ТЕКСТ ===")
print(test_response)
print("\n=== ПОСЛЕ ФОРМАТИРОВАНИЯ ===")
formatted = format_perplexity_response_with_quotes(test_response)
print(formatted) 