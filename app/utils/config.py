import configparser
import os

CONFIG_PATH = 'config.ini'

def get_config():
    """Читает и возвращает объект конфигурации."""
    config = configparser.ConfigParser()
    if not os.path.exists(CONFIG_PATH):
        raise FileNotFoundError(f"Файл конфигурации не найден по пути: {CONFIG_PATH}")
    config.read(CONFIG_PATH, encoding='utf-8')
    return config

def get_telegram_config():
    """Возвращает параметры из секции [telegram]."""
    config = get_config()
    limit = config.getint('telegram', 'limit', fallback=50)
    
    start_from_id_str = config.get('telegram', 'start_from_id', fallback=None)
    start_from_id = None
    if start_from_id_str and start_from_id_str.strip():
        try:
            start_from_id = int(start_from_id_str)
        except (ValueError, TypeError):
            print(f"Предупреждение: Неверное значение для start_from_id в config.ini: '{start_from_id_str}'. Будет проигнорировано.")
            start_from_id = None
            
    return limit, start_from_id

def get_pricing_config():
    """Возвращает параметры из секции [pricing]."""
    config = get_config()
    markup = config.getfloat('pricing', 'markup_percentage', fallback=0)
    return markup

def set_pricing_config(markup_percentage: float):
    """Устанавливает и сохраняет процент наценки в config.ini."""
    config = get_config()
    if 'pricing' not in config:
        config.add_section('pricing')
    config.set('pricing', 'markup_percentage', str(markup_percentage))
    
    with open(CONFIG_PATH, 'w', encoding='utf-8') as configfile:
        config.write(configfile)

def get_application_config():
    """Возвращает параметры из секции [application]."""
    config = get_config()
    button_text = config.get('application', 'button_text', fallback=None)
    button_url = config.get('application', 'button_url', fallback=None)
    
    # Не возвращаем текст, если нет URL
    if not button_url or not button_url.strip():
        return None, None
        
    return button_text, button_url 