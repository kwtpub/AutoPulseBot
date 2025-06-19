from datetime import datetime
from typing import Dict, Optional

class MessageFormatter:
    def __init__(self, template_path: Optional[str] = None):
        self.default_template = '''📌 Заголовок: {title}

📝 Краткое описание:
{description}

📄 Основной текст:
{main_text}

🔗 Источник: {source}

📅 Дата публикации: {date}'''
        
        self.template = self._load_template(template_path) if template_path else self.default_template
        
    def _load_template(self, path: str) -> str:
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        except:
            return self.default_template
            
    def format_message(self, data: Dict) -> str:
        # Ensure all required fields exist
        formatted_data = {
            'title': data.get('title', 'Без заголовка'),
            'description': self._quote_sections(data.get('description', 'Описание отсутствует')),
            'main_text': self._truncate_text(self._quote_sections(data.get('main_text', '')), 3000),
            'source': data.get('source', 'Источник не указан'),
            'date': data.get('date', datetime.now().strftime('%Y-%m-%d %H:%M'))
        }

        # Приводим все значения к строке
        for key in formatted_data:
            # Если main_text — dict, делаем красивый вывод
            if key == 'main_text' and isinstance(formatted_data[key], dict):
                formatted_data[key] = '\n'.join(f"{k}: {v}" for k, v in formatted_data[key].items() if v)
            elif not isinstance(formatted_data[key], str):
                formatted_data[key] = str(formatted_data[key])

        # Handle empty fields gracefully
        for key, value in formatted_data.items():
            if not value or value.strip() == '':
                formatted_data[key] = f'[{key} отсутствует]'

        return self.template.format(**formatted_data)
        
    def _truncate_text(self, text: str, max_length: int) -> str:
        if len(text) <= max_length:
            return text
        return text[:max_length-3] + '...'
        
    def validate_message_length(self, message: str) -> bool:
        # Telegram message limit is 4096 characters
        return len(message) <= 4096 

    def format_auto_data(self, data: Dict) -> str:
        """
        Формирует сообщение строго по структуре:
        Продаётся ... [Марка] [Модель] ...
        Основные характеристики: (в цитате)
        Комплектация и опции: (в цитате)
        Преимущества: (в цитате)
        Фото ...
        [Марка] [Модель] — [слоган]
        #хэштеги
        """
        # Краткое описание и основные поля
        brand = data.get('brand', '') or data.get('марка', '') or data.get('Марка', '') or data.get('model', '').split()[0] if data.get('model') else ''
        model = data.get('model', '') or data.get('модель', '') or data.get('Модель', '')
        gearbox = data.get('gearbox', '') or data.get('коробка', '') or data.get('Тип коробки передач', '')
        description = data.get('short_description', '') or data.get('description', '') or 'стильный и надёжный'
        state = data.get('state', '') or 'в отличном состоянии, полностью готов к эксплуатации!'
        # Основные характеристики
        year = data.get('year', '') or data.get('год', '') or data.get('Год выпуска', '')
        engine = data.get('engine', '') or data.get('двигатель', '') or data.get('Двигатель', '')
        power = data.get('power', '') or data.get('мощность', '') or data.get('Мощность', '')
        engine_code = data.get('engine_code', '') or data.get('Код двигателя', '')
        mileage = data.get('mileage', '') or data.get('пробег', '') or data.get('Пробег', '')
        body = data.get('body', '') or data.get('кузов', '') or data.get('Тип кузова', '')
        drive = data.get('drive', '') or data.get('привод', '') or data.get('Привод', '')
        vin = data.get('vin', '') or data.get('VIN', '')
        weight = data.get('weight', '') or data.get('масса', '') or data.get('Масса', '')
        color = data.get('interior_color', '') or data.get('цвет салона', '') or data.get('Цвет салона', '')
        seats = data.get('seats', '') or data.get('мест', '') or data.get('Мест', '')
        price = data.get('price', '') or data.get('цена', '') or data.get('Цена', '')
        # Комплектация и преимущества (списки)
        options = data.get('options', []) or data.get('комплектация', []) or data.get('Комплектация', [])
        if isinstance(options, str):
            options = [o.strip() for o in options.split('\n') if o.strip()]
        advantages = data.get('advantages', []) or data.get('преимущества', []) or data.get('Преимущества', [])
        if isinstance(advantages, str):
            advantages = [a.strip() for a in advantages.split('\n') if a.strip()]
        # Слоган
        slogan = data.get('slogan', '') or data.get('слоган', '') or 'премиум комфорт и немецкое качество по выгодной цене!'
        # Хэштеги
        hashtags = []
        if brand:
            hashtags += [f'#{brand}', f'#{brand}{model}', f'#{model}', f'#{brand}{year}', f'#{body}', f'#{gearbox}', f'#ПродажаАвто', f'#Авто{body}', f'#Авто{brand}', f'#Продажа{brand}']
        # Формируем текст
        msg = f"Продаётся {description} {brand} {model} с {gearbox} и отличной комплектацией. {state}\n\n"
        msg += "Основные характеристики:\n"
        char_lines = []
        if year: char_lines.append(f"• Год выпуска: {year}")
        if engine or power or engine_code:
            engine_str = engine
            if power: engine_str += f", {power}"
            if engine_code: engine_str += f", {engine_code}"
            char_lines.append(f"• Двигатель: {engine_str}")
        if mileage: char_lines.append(f"• Пробег: {mileage} км")
        if body: char_lines.append(f"• Кузов: {body}")
        if drive: char_lines.append(f"• Привод: {drive}")
        if vin: char_lines.append(f"• VIN: {vin}")
        if weight: char_lines.append(f"• Масса: {weight} кг")
        if color: char_lines.append(f"• Цвет салона: {color}")
        if seats: char_lines.append(f"• Мест: {seats}")
        # Блок цитаты
        if char_lines:
            msg += '\n'.join([f'> {line}' for line in char_lines]) + '\n\n'
        # Комплектация
        msg += "Комплектация и опции:\n"
        if options:
            msg += '\n'.join([f'> • {o}' for o in options]) + '\n\n'
        # Преимущества
        msg += "Преимущества:\n"
        if advantages:
            msg += '\n'.join([f'> • {a}' for a in advantages]) + '\n\n'
        msg += "Фото автомобиля прилагаются — пишите в личные сообщения для подробностей и записи на просмотр!\n\n"
        msg += f"{brand} {model} — {slogan}\n\n"
        if hashtags:
            msg += ' '.join(hashtags)
        return msg.strip()

    def _quote_sections(self, text: str) -> str:
        """
        Оборачивает блоки после заголовков в цитату (> ...), если встречаются ключевые заголовки.
        """
        if not text:
            return text
        import re
        # Список заголовков
        headers = [
            'Основные характеристики',
            'Комплектация и опции',
            'Преимущества'
        ]
        # Разбиваем текст на блоки по заголовкам
        pattern = r'(^|\n)(%s):?\n' % '|'.join(headers)
        parts = re.split(pattern, text)
        if len(parts) <= 1:
            return text  # нет заголовков
        result = []
        i = 0
        while i < len(parts):
            if parts[i] in headers:
                header = parts[i]
                # Следующий элемент — текст блока
                block = parts[i+1] if i+1 < len(parts) else ''
                # Оборачиваем каждую строку блока в цитату
                quoted = '\n'.join('> ' + line if line.strip() else '' for line in block.strip().split('\n'))
                result.append(f'{header}:\n{quoted}')
                i += 2
            else:
                # Просто текст вне секций
                if parts[i].strip():
                    result.append(parts[i].strip())
                i += 1
        return '\n\n'.join(result) 