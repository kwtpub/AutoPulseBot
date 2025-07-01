from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from datetime import datetime
from typing import Dict, Optional, List
import requests
import textwrap
import re
from dataclasses import dataclass

@dataclass
class TelegramMessageTemplate:
    """Шаблон сообщения для Telegram"""
    
    @staticmethod
    def format_chinese_car_online_sale(
        brand: str,
        model: str,
        year: str,
        mileage: str,
        price: str,
        engine: str,
        transmission: str,
        drive_type: str,
        trim: str,
        color: str,
        condition: str,
        custom_id: str,
        additional_features: List[str] = None,
        city: str = "Москва"
    ) -> str:
        """
        Формирует сообщение для онлайн-продажи китайских автомобилей
        
        Args:
            brand: Марка автомобиля
            model: Модель автомобиля
            year: Год выпуска
            mileage: Пробег
            price: Цена
            engine: Характеристики двигателя
            transmission: Коробка передач
            drive_type: Тип привода
            trim: Комплектация
            color: Цвет
            condition: Состояние
            custom_id: Уникальный ID автомобиля
            additional_features: Дополнительные опции
            city: Город
            
        Returns:
            Отформатированное сообщение для Telegram
        """
        
        # Основные характеристики
        features = additional_features or [
            "климат-контроль",
            "камера заднего вида", 
            "подогрев сидений",
            "сенсорный экран",
            "система безопасности"
        ]
        
        # Формируем сообщение в новом формате
        message = f"""🚗 {brand} {model} {year}
Custom ID: {custom_id}

💰 Цена: {price} ₽ 
Пробег: {mileage} км
Двигатель: {engine}
КПП: {transmission}
Привод: {drive_type}
Цвет: {color}
Комплектация: {trim}

✨ Преимущества китайских авто:
- Богатая комплектация уже в базе: современные опции, системы безопасности, климат-контроль, мультимедиа
- Современные технологии и стильный дизайн
- Официальная гарантия и сервисная поддержка до 5 лет
- Экономичность и надежность
- Отличное соотношение цена-качество

🔧 Состояние:
- {condition}
- Все документы в порядке, электронная передача
- Гарантия производителя

🚚 Условия покупки:
- 📦 Доставка по РФ
- 💬 Связь только в Telegram

⚡ Почему выгодно:
- Максимум опций за разумные деньги
- Просторный и комфортный салон
- Нет проблем с сервисом и запчастями

#китайскиеавто #онлайнпродажа #{brand.lower()}{model.lower().replace(' ', '')}"""

        return message
    
    @staticmethod
    def validate_message_length(message: str, max_length: int = 1024) -> bool:
        """Проверяет длину сообщения"""
        return len(message) <= max_length
    
    @staticmethod
    def extract_hashtags(message: str) -> List[str]:
        """Извлекает хештеги из сообщения"""
        return re.findall(r'#\w+', message)

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
        
        self.telegram = TelegramMessageTemplate()
        
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

    def format_car_message(self, car_data: Dict, pricing_config: Dict, application_config: Dict) -> str:
        def format_section(title, details):
            if not details:
                return ""
            items = []
            for key, value in details.items():
                if value:
                    # Проверяем, является ли значение уже отформатированной строкой (как "Год выпуска")
                    if isinstance(value, str) and value.startswith(f"<b>{key}"):
                        items.append(value)
                    else:
                        items.append(f"<b>{key}</b>: {value}")
            return f"<b>{title}</b>\n" + "\n".join(f"– {item}" for item in items) if items else ""

        sections = [
            f"<b>{car_data.get('title')}</b>",
            f"<b>Цена: {car_data.get('price')}</b> (в Минске без учёта таможенных платежей)\n",
            format_section("Краткое описание", {" автомобиля": car_data.get('description')}),
            format_section("Основные характеристики", {
                "Год выпуска": car_data.get('year'),
                "Двигатель": car_data.get('engine'),
                "Мощность": car_data.get('power'),
                "Привод": car_data.get('drive'),
                "Пробег": car_data.get('mileage'),
                "Кузов": car_data.get('body_type')
            }),
            format_section("Комплектация и опции", {k: k for k in car_data.get('options', [])}),
            format_section("Преимущества", {k: k for k in car_data.get('advantages', [])}),
            f"\n<i>{car_data.get('slogan')}</i>",
            f"\n{car_data.get('hashtags')}"
        ]

        # Убираем пустые секции и соединяем
        message = "\n\n".join(filter(None, sections))
        
        # Удаляем лишние переводы строк и пробелы
        message = "\n".join(line.strip() for line in message.split('\n') if line.strip())
        
        return message

    def format_for_telegram(self, car_data: Dict) -> str:
        """
        Форматирует данные автомобиля для Telegram
        
        Args:
            car_data: Словарь с данными автомобиля
            
        Returns:
            Отформатированное сообщение
        """
        return self.telegram.format_chinese_car_online_sale(
            brand=car_data.get('brand', ''),
            model=car_data.get('model', ''),
            year=car_data.get('year', ''),
            mileage=car_data.get('mileage', ''),
            price=car_data.get('price', ''),
            engine=car_data.get('engine', ''),
            transmission=car_data.get('transmission', ''),
            drive_type=car_data.get('drive_type', ''),
            trim=car_data.get('trim', ''),
            color=car_data.get('color', ''),
            condition=car_data.get('condition', ''),
            custom_id=car_data.get('custom_id', ''),
            additional_features=car_data.get('features', []),
            city=car_data.get('city', 'Москва')
        )
    
    def prepare_for_perplexity(self, car_data: Dict) -> Dict:
        """
        Подготавливает данные для отправки в Perplexity API
        
        Args:
            car_data: Исходные данные автомобиля
            
        Returns:
            Обработанные данные
        """
        return {
            'brand': car_data.get('brand', '').strip(),
            'model': car_data.get('model', '').strip(),
            'year': str(car_data.get('year', '')),
            'mileage': str(car_data.get('mileage', '')),
            'price': str(car_data.get('price', '')),
            'engine': car_data.get('engine', '').strip(),
            'transmission': car_data.get('transmission', '').strip(),
            'drive_type': car_data.get('drive_type', '').strip(),
            'trim': car_data.get('trim', '').strip(),
            'color': car_data.get('color', '').strip(),
            'condition': car_data.get('condition', 'Хорошее').strip(),
            'custom_id': car_data.get('custom_id', ''),
            'city': car_data.get('city', 'Москва').strip()
        }

async def send_message_to_telegram(bot, chat_id, text, photo_url=None):
    """
    Отправляет форматированное сообщение в Telegram, объединяя фото и текст.
    """
    try:
        if photo_url:
            # Если текст для подписи слишком длинный, отправляем его отдельным сообщением
            if len(text) > 1024:
                await bot.send_photo(
                    chat_id=chat_id,
                    photo=photo_url
                )
                # Отправляем текст после фото
                for i in range(0, len(text), 4096):
                    chunk = text[i:i+4096]
                    await bot.send_message(
                        chat_id=chat_id,
                        text=chunk,
                        parse_mode='HTML',
                        disable_web_page_preview=True
                    )
            else:
                # Если текст помещается в подпись, отправляем вместе
                await bot.send_photo(
                    chat_id=chat_id,
                    photo=photo_url,
                    caption=text,
                    parse_mode='HTML'
                )
            print(f"Сообщение с фото для чата {chat_id} успешно отправлено.")
        else:
            # Отправка обычного текстового сообщения (разбиваем на части, если нужно)
            for i in range(0, len(text), 4096):
                chunk = text[i:i+4096]
                await bot.send_message(
                    chat_id=chat_id,
                    text=chunk,
                    parse_mode='HTML',
                    disable_web_page_preview=True
                )
            print(f"Текстовое сообщение для чата {chat_id} успешно отправлено.")
            
    except Exception as e:
        print(f"Ошибка при отправке сообщения в чат {chat_id}: {e}") 