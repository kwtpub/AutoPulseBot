"""
Text Formatter - форматирование текста и создание промптов для объявлений об автомобилях
Специализированные функции для создания привлекательных описаний автомобилей
"""

import re
from typing import Dict, Optional, Tuple, List
from dataclasses import dataclass
from datetime import datetime
from app.utils.cbr_exchange_rate import get_cbr_usd_rate_with_markup

@dataclass
class CarInfo:
    """Структура данных об автомобиле"""
    brand: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    price: Optional[float] = None
    mileage: Optional[int] = None
    engine_volume: Optional[str] = None
    transmission: Optional[str] = None
    drive_type: Optional[str] = None
    body_type: Optional[str] = None
    color: Optional[str] = None
    fuel_type: Optional[str] = None
    trim: Optional[str] = None
    condition: Optional[str] = None
    custom_id: Optional[str] = None

def extract_car_info_from_text(text: str) -> CarInfo:
    """
    Извлекает информацию об автомобиле из текста объявления
    Многоэтапная система с несколькими уровнями fallback
    
    Args:
        text: Текст объявления
        
    Returns:
        CarInfo с извлеченными данными
    """
    print(f"🔍 ЭТАП 0: Входной текст ({len(text)} символов):\n{text[:300]}...")
    
    car_info = CarInfo()
    text_lower = text.lower()
    
    # Подготавливаем строки для анализа
    lines = [line.strip() for line in text.strip().split('\n') if line.strip()]
    first_line = lines[0] if lines else ""
    
    print(f"🔍 ЭТАП 1: Анализ первой строки: '{first_line}'")
    
    # Расширенный список марок с вариантами написания
    brands_mapping = {
        # Китайские марки
        'geely': ['geely', 'джили', 'гили'],
        'chery': ['chery', 'чери', 'черри'],
        'byd': ['byd', 'бид', 'би-ай-ди'],
        'haval': ['haval', 'хавал', 'хаваль'],
        'great wall': ['great wall', 'грейт волл', 'великая стена'],
        'changan': ['changan', 'чанган', 'чангань'],
        'dongfeng': ['dongfeng', 'донгфенг'],
        'faw': ['faw', 'фав'],
        'jac': ['jac', 'жак', 'джак'],
        'lifan': ['lifan', 'лифан'],
        'zotye': ['zotye', 'зотье'],
        'brilliance': ['brilliance', 'бриллианс'],
        'foton': ['foton', 'фотон'],
        'maxus': ['maxus', 'максус'],
        'tank': ['tank', 'танк'],
        'ora': ['ora', 'ора'],
        'nio': ['nio', 'нио'],
        'xpeng': ['xpeng', 'икспенг'],
        'hongqi': ['hongqi', 'хунци'],
        'gac': ['gac', 'гак'],
        'roewe': ['roewe', 'роеве'],
        'mg': ['mg', 'мг'],
        'baojun': ['baojun', 'баоцзюнь'],
        'wuling': ['wuling', 'вулинг'],
        'lynk': ['lynk', 'линк'],
        'lixiang': ['lixiang', 'лисян', 'лисянг', 'li xiang'],
        # Составные европейские/премиум
        'mercedes-benz': ['mercedes-benz', 'мерседес-бенц', 'mercedes benz'],
        'land rover': ['land rover', 'лэнд ровер', 'ленд ровер'],
        'range rover': ['range rover', 'рэндж ровер', 'рейндж ровер'],
        'rolls-royce': ['rolls-royce', 'роллс-ройс', 'rolls royce'],
        'alfa romeo': ['alfa romeo', 'альфа ромео'],
        'aston martin': ['aston martin', 'астон мартин'],
        'mini cooper': ['mini cooper', 'мини купер'],
        # Европейские
        'audi': ['audi', 'ауди'],
        'bmw': ['bmw', 'бмв'],
        'volkswagen': ['volkswagen', 'фольксваген', 'vw'],
        'opel': ['opel', 'опель'],
        'peugeot': ['peugeot', 'пежо'],
        'renault': ['renault', 'рено'],
        'skoda': ['skoda', 'шкода'],
        'citroen': ['citroen', 'ситроен', 'ситроэн'],
        'fiat': ['fiat', 'фиат'],
        'seat': ['seat', 'сеат'],
        'volvo': ['volvo', 'вольво'],
        'saab': ['saab', 'сааб'],
        'smart': ['smart', 'смарт'],
        'dacia': ['dacia', 'дачия', 'дача'],
        'lancia': ['lancia', 'ланча', 'лансия'],
        'lotus': ['lotus', 'лотус'],
        'porsche': ['porsche', 'порше'],
        'jaguar': ['jaguar', 'ягуар'],
        'bentley': ['bentley', 'бентли'],
        'bugatti': ['bugatti', 'бугатти'],
        'maserati': ['maserati', 'масерати'],
        'ferrari': ['ferrari', 'феррари'],
        'lamborghini': ['lamborghini', 'ламборгини'],
        'mini': ['mini', 'мини'],
        # Японские
        'toyota': ['toyota', 'тойота'],
        'honda': ['honda', 'хонда'],
        'nissan': ['nissan', 'ниссан'],
        'mazda': ['mazda', 'мазда'],
        'mitsubishi': ['mitsubishi', 'митсубиси', 'мицубиси'],
        'subaru': ['subaru', 'субару'],
        'suzuki': ['suzuki', 'сузуки'],
        'lexus': ['lexus', 'лексус'],
        'infiniti': ['infiniti', 'инфинити'],
        'acura': ['acura', 'акура'],
        'daihatsu': ['daihatsu', 'дайхатсу'],
        'isuzu': ['isuzu', 'исузу'],
        # Корейские
        'hyundai': ['hyundai', 'хюндай', 'хендай'],
        'kia': ['kia', 'киа'],
        'ssangyong': ['ssangyong', 'ссангйонг', 'сангёнг'],
        'genesis': ['genesis', 'генезис'],
        'daewoo': ['daewoo', 'дэу', 'деу'],
        # Американские
        'ford': ['ford', 'форд'],
        'chevrolet': ['chevrolet', 'шевроле'],
        'cadillac': ['cadillac', 'кадиллак'],
        'chrysler': ['chrysler', 'крайслер'],
        'dodge': ['dodge', 'додж'],
        'jeep': ['jeep', 'джип'],
        'lincoln': ['lincoln', 'линкольн'],
        'buick': ['buick', 'бьюик'],
        'gmc': ['gmc', 'джиэмси'],
        'hummer': ['hummer', 'хаммер'],
        'tesla': ['tesla', 'тесла'],
        'ram': ['ram', 'рам'],
        # Российские
        'lada': ['lada', 'ваз', 'лада'],
        'uaz': ['uaz', 'уаз'],
        'gaz': ['gaz', 'газ'],
        'volga': ['volga', 'волга'],
        'moskvich': ['moskvich', 'москвич'],
        'zaz': ['zaz', 'заз'],
        'luaz': ['luaz', 'луаз'],
        # Прочие
        'mercedes': ['mercedes'],  # Одиночный mercedes в конце списка
        # Экзотика, редкие, нишевые, новые электромобили и др.
        'aixam': ['aixam', 'айксам'],
        'ariel': ['ariel', 'ариэль'],
        'baic': ['baic', 'байк'],
        'baw': ['baw', 'бав'],
        'belgee': ['belgee', 'белджи', 'белджи'],
        'borgward': ['borgward', 'боргвард'],
        'brabus': ['brabus', 'брабус'],
        'bufori': ['bufori', 'буфори'],
        'byton': ['byton', 'байтон'],
        'changhe': ['changhe', 'чанхе'],
        'datsun': ['datsun', 'датсун'],
        'derways': ['derways', 'дервейс'],
        'dfm': ['dfm', 'дфм'],
        'dr': ['dr', 'др'],
        'ds': ['ds', 'дс'],
        'exeed': ['exeed', 'эксид'],
        'fisker': ['fisker', 'фискер'],
        'haima': ['haima', 'хайма'],
        'hino': ['hino', 'хино'],
        'iran khodro': ['iran khodro', 'иран ходро'],
        'jetour': ['jetour', 'жетур'],
        'jmc': ['jmc', 'джмс'],
        'kamaz': ['kamaz', 'камаз'],
        'king long': ['king long', 'кинг лонг'],
        'landwind': ['landwind', 'лэндвинд'],
        'leapmotor': ['leapmotor', 'липмотор'],
        'mahindra': ['mahindra', 'махиндра'],
        'maruti': ['maruti', 'марути'],
        'maybach': ['maybach', 'майбах'],
        'microcar': ['microcar', 'микрокар'],
        'moskvich': ['moskvich', 'москвич'],
        'nio': ['nio', 'нио'],
        'perodua': ['perodua', 'перодуа'],
        'proton': ['proton', 'протон'],
        'ravon': ['ravon', 'равон'],
        'saipa': ['saipa', 'сайпа'],
        'scion': ['scion', 'сайон'],
        'shineray': ['shineray', 'шайнерей'],
        'ssangyong': ['ssangyong', 'ссангйонг', 'сангёнг'],
        'tata': ['tata', 'тата'],
        'vortex': ['vortex', 'вортекс'],
        'weling': ['weling', 'велинг'],
        'zotye': ['zotye', 'зотье'],
        'zx': ['zx', 'зх'],
        # Электромобили и новые бренды
        'neta': ['neta', 'нета'],
        'seres': ['seres', 'серес'],
        'voyah': ['voyah', 'воя'],
        'skywell': ['skywell', 'скайвелл'],
        'weltmeister': ['weltmeister', 'вельтмайстер'],
        'wm motor': ['wm motor', 'вм мотор'],
        'zeekr': ['zeekr', 'зикр'],
        # Индийские и малайзийские
        'perodua': ['perodua', 'перодуа'],
        # Редкие европейские
        'dr': ['dr', 'др'],
        'ds': ['ds', 'дс'],
        'belgee': ['belgee', 'белджи', 'белджи'],
        # Кастом/тюнинг
        'mansory': ['mansory', 'мансори'],
        'hamann': ['hamann', 'хаман'],
        'g-power': ['g-power', 'джи-пауэр', 'g power'],
    }
    
    # ЭТАП 1: Поиск марки в первой строке (сначала составные марки)
    found_brand = None
    brand_variants = None
    first_line_lower = first_line.lower()
    # Составляем список составных марок (2-3 слова)
    sorted_brands = sorted(brands_mapping.items(), key=lambda x: -max(len(v.split()) for v in x[1]))
    for brand_key, variants in sorted_brands:
        for variant in variants:
            variant_clean = variant.replace('-', ' ').lower()
            # Ищем как есть и без дефиса
            if variant in first_line_lower or variant_clean in first_line_lower.replace('-', ' '):
                found_brand = brand_key
                brand_variants = variants
                print(f"✅ ЭТАП 1: Найдена марка '{brand_key}' (вариант '{variant}') в первой строке")
                break
        if found_brand:
            break
    # Если найдена марка в первой строке, извлекаем модель
    if found_brand:
        # Ищем позицию марки
        brand_pos = -1
        used_variant = None
        for variant in brand_variants:
            pos = first_line_lower.find(variant)
            if pos == -1:
                # Пробуем без дефиса
                pos = first_line_lower.replace('-', ' ').find(variant.replace('-', ' '))
            if pos != -1:
                brand_pos = pos
                used_variant = variant
                break
        if brand_pos != -1:
            # Извлекаем часть после марки
            after_brand = first_line[brand_pos + len(used_variant):].strip()
            # Убираем год если есть
            model_clean = re.sub(r'\s*(19|20)\d{2}.*', '', after_brand).strip()
            # Убираем лишние символы
            model_clean = re.sub(r'[^\w\s-]', '', model_clean).strip()
            # Убираем служебные слова из модели
            service_words_model = {'год', 'тип', 'комплектация', 'бизнес', 'класс', 'тип', 'new', 'новый', 'без', 'учета', 'таможенных', 'таможни', 'авто', 'машина', 'car', 'auto'}
            model_words = [w for w in model_clean.split() if w.lower() not in service_words_model]
            car_info.brand = found_brand.title()
            car_info.model = ' '.join(model_words) if model_words else "Неизвестная модель"
            print(f"✅ ЭТАП 1: Марка={car_info.brand}, Модель={car_info.model}")
    
    # ЭТАП 2: Если не найдено - поиск по паттернам
    if not car_info.brand:
        print("🔍 ЭТАП 2: Поиск через регулярные выражения")
        
        patterns = [
            r'^([A-Za-zА-Яа-я-]+)\s+([A-Za-zА-Яа-я0-9\s-]+?)\s*(\d{4})',  # Марка Модель Год
            r'^([A-Za-zА-Яа-я-]+)\s+([A-Za-zА-Яа-я0-9\s-]+)',  # Марка Модель
            r'([A-Za-zА-Яа-я-]+)\s+([A-Za-zА-Яа-я0-9\s-]+?)\s*(\d{4})',  # Марка Модель Год (в любом месте)
        ]
        
        for i, pattern in enumerate(patterns):
            match = re.search(pattern, first_line)
            if match:
                potential_brand = match.group(1).strip()
                potential_model = match.group(2).strip()
                
                # Проверяем, что это не служебные слова
                service_words = ['продам', 'продается', 'авто', 'автомобиль', 'машина', 'цена', 'год', 'состояние']
                if potential_brand.lower() not in service_words and len(potential_brand) > 2:
                    car_info.brand = potential_brand.title()
                    car_info.model = potential_model
                    print(f"✅ ЭТАП 2.{i+1}: Найдено через паттерн - Марка={car_info.brand}, Модель={car_info.model}")
                    break
    
    # ЭТАП 3: Поиск марки по всему тексту
    if not car_info.brand:
        print("🔍 ЭТАП 3: Поиск марки по всему тексту")
        text_lower = text.lower()
        service_words_model = {'год', 'тип', 'комплектация', 'бизнес', 'класс', 'тип', 'new', 'новый', 'без', 'учета', 'таможенных', 'таможни', 'авто', 'машина', 'car', 'auto'}
        for brand_key, variants in brands_mapping.items():
            for variant in variants:
                pattern = rf'\b{re.escape(variant)}\b'
                match = re.search(pattern, text_lower)
                if match:
                    car_info.brand = brand_key.title()
                    # Пытаемся найти модель рядом
                    after = text[match.end():].strip().split()
                    model_words = []
                    for w in after:
                        if re.match(r'^(19|20)\d{2}$', w): break
                        if w.lower() in service_words_model: break
                        model_words.append(w)
                        if len(model_words) >= 2: break
                    car_info.model = ' '.join(model_words) if model_words else 'Неизвестная модель'
                    print(f"✅ ЭТАП 3: Найдено в тексте - Марка={car_info.brand}, Модель={car_info.model}")
                    break
            if car_info.brand:
                break
    
    # ЭТАП 4: Экстренный fallback - берем первые подходящие слова
    if not car_info.brand:
        print("🔍 ЭТАП 4: Экстренный fallback")
        # Очищаем первую строку от мусора
        clean_line = re.sub(r'[^-а-яА-ЯёЁ\s-]', ' ', first_line)
        words = [w for w in clean_line.split() if w.isalpha() and len(w) > 2]
        # Расширенный список стоп-слов
        service_words = {
            'продам', 'продается', 'авто', 'автомобиль', 'машина', 'цена', 'год', 'состояние', 'пробег',
            'минск', 'минске', 'без', 'в', 'на', 'купить', 'продажа', 'новый', 'б/у', 'комплектация',
            'цвет', 'документы', 'объявление', 'или', 'и', 'с', 'по', 'за', 'от', 'до', 'новая', 'новое',
            'новые', 'новых', 'нового', 'новой', 'новым', 'новыми', 'новых', 'новое', 'новая', 'новый',
            'новое', 'новая', 'новый', 'новое', 'новая', 'новый', 'новое', 'новая', 'новый', 'новое',
        }
        filtered_words = [w for w in words if w.lower() not in service_words]
        if len(filtered_words) >= 2:
            car_info.brand = filtered_words[0].title()
            car_info.model = filtered_words[1].title()
            print(f"✅ ЭТАП 4: Fallback - Марка={car_info.brand}, Модель={car_info.model}")
        elif len(filtered_words) == 1:
            car_info.brand = filtered_words[0].title()
            car_info.model = "Неизвестная модель"
            print(f"✅ ЭТАП 4: Fallback - только марка={car_info.brand}")
        else:
            car_info.brand = "Автомобиль"
            car_info.model = "Неизвестная модель"
            print(f"✅ ЭТАП 4: Fallback - нет валидных слов, возвращаю дефолт")
    
    # ЭТАП 5: Последний fallback
    if not car_info.brand:
        print("🔍 ЭТАП 5: Последний fallback - используем дефолтные значения")
        car_info.brand = "Автомобиль"
        car_info.model = "Неизвестная модель"
    
    print(f"🎯 ИТОГ: Марка='{car_info.brand}', Модель='{car_info.model}'")
    
    # Извлечение года (4 цифры от 1980 до текущего года + 2)
    current_year = datetime.now().year
    year_pattern = r'\b(19[8-9]\d|20[0-2]\d)\b'
    year_match = re.search(year_pattern, text)
    if year_match:
        year = int(year_match.group(1))
        if 1980 <= year <= current_year + 2:
            car_info.year = year
            print(f"✅ Найден год: {car_info.year}")
    
    # Извлечение цены в долларах США
    print("🔍 Поиск цены в долларах...")
    price_patterns = [
        r'(\d{1,3}(?:\s\d{3})*)\s*\$',  # 40 400$ (с пробелами)
        r'\$(\d{1,3}(?:,\d{3})*)',  # $25,000
        r'(\d{1,3}(?:,\d{3})*)\s*\$',  # 25,000$
        r'(\d{1,3}(?:,\d{3})*)\s*долл',  # 25000 долл
        r'(\d+)\s*тыс.*долл',  # 25 тыс долл
        r'price.*\$(\d{1,3}(?:,\d{3})*)',  # price: $25,000
        r'цена.*(\d{1,3}(?:,\d{3})*)\s*\$',  # цена 25,000$
    ]
    
    for i, pattern in enumerate(price_patterns):
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            price_str = match.group(1).replace(',', '').replace(' ', '')  # Убираем запятые и пробелы
            print(f"🔍 Найден паттерн {i+1}: '{match.group(0)}' -> '{price_str}'")
            try:
                price = int(price_str)
                # Обработка "тыс долл"
                if 'тыс' in match.group(0).lower():
                    price *= 1000
                    
                if 5000 <= price <= 500000:  # Разумные пределы для цены авто
                    car_info.price = price
                    print(f"✅ Найдена цена: ${car_info.price}")
                    break
                else:
                    print(f"❌ Цена {price} вне разумных пределов")
            except ValueError:
                print(f"❌ Ошибка парсинга цены: {price_str}")
                continue
    
    # Извлечение пробега
    print("🔍 Поиск пробега...")
    mileage_patterns = [
        r'(\d{1,3}(?:,\d{3})*)\s*км',  # 150,000 км
        r'пробег.*?(\d{1,3}(?:,\d{3})*)',  # пробег: 150000
        r'(\d+)\s*тыс.*км',  # 150 тыс км
        r'mileage.*?(\d{1,3}(?:,\d{3})*)',  # mileage: 150000
    ]
    
    for pattern in mileage_patterns:
        match = re.search(pattern, text_lower)
        if match:
            mileage_str = match.group(1).replace(',', '')
            try:
                mileage = int(mileage_str)
                # Обработка "тыс км"
                if 'тыс' in match.group(0):
                    mileage *= 1000
                    
                if 0 <= mileage <= 1000000:  # Разумные пределы для пробега
                    car_info.mileage = mileage
                    print(f"✅ Найден пробег: {car_info.mileage} км")
                    break
            except ValueError:
                continue
    
    # Извлечение информации о двигателе
    engine_patterns = [
        r'(\d\.?\d?)\s*[лl]',  # 2.0л или 2л
        r'двигат.*?(\d\.?\d?)\s*[лl]',  # двигатель 2.0л
        r'engine.*?(\d\.?\d?)\s*[lL]',  # engine 2.0L
    ]
    
    for pattern in engine_patterns:
        match = re.search(pattern, text_lower)
        if match:
            car_info.engine_volume = f"{match.group(1)}л"
            print(f"✅ Найден объем двигателя: {car_info.engine_volume}")
            break
    
    # Извлечение коробки передач
    transmission_keywords = {
        'автомат': ['автомат', 'automatic', 'акпп', 'auto'],
        'механика': ['механика', 'manual', 'мкпп', 'мех'],
        'вариатор': ['вариатор', 'cvt'],
        'робот': ['робот', 'dsg', 'amt']
    }
    
    for trans_type, keywords in transmission_keywords.items():
        for keyword in keywords:
            if keyword in text_lower:
                car_info.transmission = trans_type
                print(f"✅ Найдена КПП: {car_info.transmission}")
                break
        if car_info.transmission:
            break
    
    # Извлечение типа привода
    drive_keywords = {
        'полный': ['полный', 'awd', '4wd', 'quattro'],
        'передний': ['передний', 'fwd', 'front'],
        'задний': ['задний', 'rwd', 'rear']
    }
    
    for drive_type, keywords in drive_keywords.items():
        for keyword in keywords:
            if keyword in text_lower:
                car_info.drive_type = drive_type
                print(f"✅ Найден привод: {car_info.drive_type}")
                break
        if car_info.drive_type:
            break
    
    print(f"🏁 ФИНАЛЬНЫЕ ДАННЫЕ:")
    print(f"   Марка: {car_info.brand}")
    print(f"   Модель: {car_info.model}")
    print(f"   Год: {car_info.year}")
    print(f"   Цена: ${car_info.price}")
    print(f"   Пробег: {car_info.mileage} км")
    print(f"   Двигатель: {car_info.engine_volume}")
    print(f"   КПП: {car_info.transmission}")
    print(f"   Привод: {car_info.drive_type}")
    
    return car_info

def create_car_description_prompt(car_info: CarInfo, custom_context: str = "") -> str:
    """
    Создает промпт для Perplexity API для генерации объявления о продаже китайского автомобиля
    
    Args:
        car_info: Информация об автомобиле
        custom_context: Дополнительный контекст
        
    Returns:
        Строка с промптом для API
    """
    
    # Получаем цену в рублях и округляем до 100
    price_rub = None
    if car_info.price:
        rate = get_cbr_usd_rate_with_markup(2.0)
        if rate:
            price_rub = int(round(car_info.price * rate / 100) * 100)
    price_rub_str = f"{price_rub:,} ₽" if price_rub else "Цена не указана"
    
    # Технический промпт для генерации объявления
    prompt = f"""Создай техническое объявление для продажи автомобиля в формате HTML для Telegram. 

ИСХОДНЫЕ ДАННЫЕ:
- Марка/модель: {car_info.brand} {car_info.model}
- Год: {car_info.year}
- Пробег: {car_info.mileage} км
- Цена: {price_rub_str}
- Двигатель: {car_info.engine_volume}
- КПП: {car_info.transmission}
- Привод: {car_info.drive_type}
- Комплектация: {car_info.trim}
- Цвет: {car_info.color}
- Состояние: {car_info.condition}

СТРУКТУРА ОБЪЯВЛЕНИЯ:
1. Заголовок: 🚗 <b>[Марка] [Модель] [Год]</b>
2. Технические характеристики в <blockquote>
3. Состояние и документы
4. Цена в рублях с пометкой (в Минске, без таможенных платежей)
5. Дополнительные детали (системы, мультимедиа, практичные опции)
6. Хештеги
7. CAR ID: <b>CAR ID:</b> <code>{car_info.custom_id or 'авто-онлайн'}</code>

ТРЕБОВАНИЯ ПО ФОРМАТИРОВАНИЮ:
- Используй ТОЛЬКО HTML-теги: <b></b>, <i></i>, <blockquote></blockquote>, <code></code>
- НЕ используй Markdown (**, *, #, -, >)
- Заголовки разделов делай жирными: <b>🔍 Технические характеристики:</b>
- Характеристики оборачивай в <blockquote>Двигатель: 2.0л
КПП: автомат</blockquote>
- Каждый раздел с новой строки

ПРИМЕР ПРАВИЛЬНОГО ФОРМАТИРОВАНИЯ:
🚗 <b>Geely Coolray 2023</b>
<b>🔍 Технические характеристики:</b>
<blockquote>Двигатель: 2.0 л, бензин, 245 л.с.
КПП: Автоматическая
Привод: Полный
Пробег: 50,000 км</blockquote>

<b>📝 Состояние и документы:</b>
Состояние: Хорошее
Документы: В наличии

ТЕХНИЧЕСКИЕ ДЕТАЛИ К ДОБАВЛЕНИЮ:
- Точные характеристики двигателя и трансмиссии
- Системы безопасности и помощи водителю
- Мультимедиа и connectivity (CarPlay/Android Auto)
- Практичные опции (климат, подогревы, датчики)
- Размеры багажника и клиренс
- Экономичность (расход топлива)

{custom_context}

ВАЖНО: 
- Цена указана в рублях (RUB)
- НЕ используй никаких Markdown символов
- Все жирное форматирование через <b></b>
- Технические характеристики ТОЛЬКО в <blockquote></blockquote>

CAR ID всегда указывай в самом конце объявления, отдельной строкой:
<b>CAR ID:</b> <code>{car_info.custom_id or 'авто-онлайн'}</code>

Создай краткое техническое объявление до 900 символов."""

    return prompt

def format_car_announcement(
    brand: str,
    model: str,
    year: int,
    price: float,
    description: str,
    characteristics: Dict[str, str],
    hashtags: List[str] = None
) -> str:
    """
    Форматирует финальное объявление об автомобиле
    
    Args:
        brand: Марка автомобиля
        model: Модель автомобиля  
        year: Год выпуска
        price: Цена
        description: Описание
        characteristics: Словарь характеристик
        hashtags: Список хэштегов
        
    Returns:
        Отформатированное объявление
    """
    
    # Форматирование цены
    price_formatted = f"{int(price):,}".replace(',', ' ')
    
    # Заголовок
    header = f"[{brand}] [{model}] [{year}] - Цена: {price_formatted} ₽"
    
    # Описание
    desc_section = f"💫 {description}"
    
    # Характеристики
    char_lines = []
    if characteristics:
        char_lines.append("📋 Основные характеристики:")
        
        # Группируем характеристики по строкам
        main_chars = []
        if 'year' in characteristics:
            main_chars.append(f"Год: {characteristics['year']}")
        if 'engine' in characteristics:
            main_chars.append(f"Двигатель: {characteristics['engine']}")
        if 'mileage' in characteristics:
            main_chars.append(f"Пробег: {characteristics['mileage']}")
        
        if main_chars:
            char_lines.append("• " + " | ".join(main_chars))
        
        # Вторая строка характеристик
        second_chars = []
        if 'transmission' in characteristics:
            second_chars.append(f"Коробка: {characteristics['transmission']}")
        if 'drive' in characteristics:
            second_chars.append(f"Привод: {characteristics['drive']}")
        if 'body' in characteristics:
            second_chars.append(f"Кузов: {characteristics['body']}")
            
        if second_chars:
            char_lines.append("• " + " | ".join(second_chars))
    
    # Слоган
    slogan = f"🚗 {brand} {model} — надежность и качество!"
    
    # Хэштеги
    if not hashtags:
        hashtags = [
            f"#{brand.lower()}", 
            f"#{model.lower().replace(' ', '')}", 
            f"#{year}",
            "#автомобиль", 
            "#продажа"
        ]
    
    hashtag_line = " ".join(hashtags)
    
    # Сборка финального текста
    sections = [header, "", desc_section]
    
    if char_lines:
        sections.append("")
        sections.extend(char_lines)
    
    sections.extend(["", slogan, "", hashtag_line])
    
    return "\n".join(sections)

def apply_markup_to_price(original_price: float, markup_percentage: float) -> float:
    """
    Применяет наценку к цене
    
    Args:
        original_price: Исходная цена
        markup_percentage: Процент наценки
        
    Returns:
        Цена с наценкой
    """
    return original_price * (1 + markup_percentage / 100)

def format_price_with_markup(car_info: CarInfo, markup_percentage: float = 15.0) -> str:
    """
    Форматирует цену с наценкой в долларах
    
    Args:
        car_info: Информация об автомобиле с ценой
        markup_percentage: Процент наценки
        
    Returns:
        Отформатированная цена с наценкой в долларах
    """
    if not car_info.price:
        return "Цена не указана"
    
    # Применяем наценку
    final_price = apply_markup_to_price(car_info.price, markup_percentage)
    
    # Форматируем в долларах
    return f"${final_price:,.0f}"

def validate_car_announcement_format(text: str) -> Tuple[bool, str]:
    """
    Проверяет соответствие текста требуемому формату объявления
    
    Args:
        text: Текст для проверки
        
    Returns:
        Tuple[bool, str]: (валидность, сообщение об ошибке)
    """
    
    lines = text.strip().split('\n')
    if not lines:
        return False, "Пустой текст"
    
    first_line = lines[0].strip()
    
    # Проверка формата первой строки
    pattern = r'^\[.+\]\s*\[.+\]\s*\[\d{4}\]\s*-\s*Цена:\s*[\d\s]+.*₽?'
    
    if not re.match(pattern, first_line):
        return False, f"Первая строка не соответствует формату [Марка] [Модель] [Год] - Цена: [цена]. Получено: {first_line}"
    
    return True, "Формат корректен"

def extract_structured_data_from_announcement(text: str) -> Dict[str, str]:
    """
    Извлекает структурированные данные из отформатированного объявления
    
    Args:
        text: Отформатированный текст объявления
        
    Returns:
        Словарь с извлеченными данными
    """
    data = {}
    
    lines = text.strip().split('\n')
    if not lines:
        return data
    
    # Извлечение из первой строки
    first_line = lines[0].strip()
    header_pattern = r'^\[(.+?)\]\s*\[(.+?)\]\s*\[(\d{4})\]\s*-\s*Цена:\s*([\d\s]+)'
    
    header_match = re.match(header_pattern, first_line)
    if header_match:
        data['brand'] = header_match.group(1)
        data['model'] = header_match.group(2)
        data['year'] = header_match.group(3)
        data['price'] = header_match.group(4).replace(' ', '')
    
    # Извлечение характеристик
    for line in lines:
        if '|' in line and ('Год:' in line or 'Двигатель:' in line):
            # Парсинг строки характеристик
            parts = [part.strip() for part in line.split('|')]
            for part in parts:
                if ':' in part:
                    key_value = part.split(':', 1)
                    if len(key_value) == 2:
                        key = key_value[0].strip().replace('• ', '')
                        value = key_value[1].strip()
                        data[key.lower()] = value
    
    return data

def convert_usd_to_rub_with_cbr(usd: float, markup: float = 2.0) -> int:
    """
    Конвертирует сумму в USD в рубли по курсу ЦБ РФ + наценка (по умолчанию 2%)
    """
    rate = get_cbr_usd_rate_with_markup(markup)
    if rate and usd:
        return int(round(usd * rate))
    return 0 