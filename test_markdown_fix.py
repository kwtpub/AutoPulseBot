#!/usr/bin/env python3
"""
Тест исправления Markdown разметки в ответе Perplexity
"""

from app.utils.announcement_processor import format_perplexity_response_with_quotes

def test_markdown_fix():
    """Тестирует исправление Markdown разметки из реального примера"""
    
    # Реальный пример от пользователя
    real_example = """🚗 Не указана Не указана 2025  
Custom ID: 160-415

🛠️ **Технические характеристики**  
- Двигатель: 2.0 л, бензин, турбо, 245 л.с.  
- Коробка передач: автомат  
- Привод: полный (4WD)  
- Пробег: 50 000 км  
- Комплектация: комфорт  
- Расход топлива: 6.5–7.5 л/100 км (для 2.0 л бензиновых двигателей аналогичного класса)[1]  
- Клиренс: 180–200 мм (типовое значение для SUV этого сегмента)  
- Объем багажника: 500–550 л (типовое значение для SUV 2.0 AWD)  

🛡️ **Системы безопасности и помощи**  
- ABS, ESP  
- Мульти-эйрбэг  
- Ассистент удержания полосы  
- Датчики света и дождя  
- Камера заднего вида, парктроники  

📱 **Мультимедиа и опции**  
- Дисплей 10.25"  
- Поддержка Apple CarPlay / Android Auto[1]  
- Круиз-контроль  
- Климат-контроль  
- Подогрев сидений  
- Датчики парковки  

📄 **Состояние и документы**  
- Состояние: хорошее  
- Документы: полный комплект  

💳 **Условия продажи**  
- Только онлайн  
- Доставка  
- Безналичный расчет  
- Цена: 46 816 USD  

#авто2025 #2литра #полныйпривод #а..."""

    print("📋 ТЕСТ ИСПРАВЛЕНИЯ MARKDOWN РАЗМЕТКИ")
    print("=" * 60)
    
    print("\n🔹 Исходный пример (с Markdown):")
    print(real_example[:500] + "..." if len(real_example) > 500 else real_example)
    
    print("\n🔹 После обработки:")
    formatted_response = format_perplexity_response_with_quotes(real_example)
    
    # Показываем только секцию с техническими характеристиками
    lines = formatted_response.split('\n')
    tech_start = -1
    tech_end = -1
    
    for i, line in enumerate(lines):
        if 'технические характеристики' in line.lower():
            tech_start = i
        elif tech_start != -1 and line.strip().startswith('🛡'):
            tech_end = i
            break
    
    if tech_start != -1:
        if tech_end == -1:
            tech_end = len(lines)
        tech_section = '\n'.join(lines[tech_start:tech_end]).strip()
        print(tech_section)
    else:
        print("Секция не найдена")
    
    print("\n🔹 Проверка результата:")
    if "<blockquote>" in formatted_response:
        print("✅ HTML blockquote добавлен")
        
        # Проверяем что Markdown убран
        blockquote_content = formatted_response[formatted_response.find('<blockquote>'):formatted_response.find('</blockquote>') + 12]
        if '**' not in blockquote_content and not any(line.strip().startswith('- ') for line in blockquote_content.split('\n')):
            print("✅ Markdown разметка очищена")
        else:
            print("❌ Markdown разметка осталась")
            
    else:
        print("❌ HTML blockquote не найден")

if __name__ == "__main__":
    test_markdown_fix() 