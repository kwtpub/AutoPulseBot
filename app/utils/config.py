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