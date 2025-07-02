import requests
import xml.etree.ElementTree as ET
from typing import Optional

def get_cbr_usd_rate() -> Optional[float]:
    """
    Получает актуальный курс доллара США с сайта ЦБ РФ (https://www.cbr.ru/scripts/XML_daily.asp)
    
    Returns:
        Курс доллара (float) или None при ошибке
    """
    try:
        url = "https://www.cbr.ru/scripts/XML_daily.asp"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        tree = ET.fromstring(response.content)
        for valute in tree.findall('Valute'):
            char_code = valute.find('CharCode').text
            if char_code == 'USD':
                value = valute.find('Value').text.replace(',', '.')
                return float(value)
        return None
    except Exception as e:
        print(f"Ошибка получения курса USD с ЦБ РФ: {e}")
        return None

def get_cbr_usd_rate_with_markup(markup_percent: float = 2.0) -> Optional[float]:
    """
    Возвращает курс доллара с ЦБ РФ с наценкой (по умолчанию 2%)
    """
    base_rate = get_cbr_usd_rate()
    if base_rate is not None:
        return round(base_rate * (1 + markup_percent / 100), 4)
    return None

if __name__ == "__main__":
    rate = get_cbr_usd_rate()
    rate_markup = get_cbr_usd_rate_with_markup()
    if rate:
        print(f"Актуальный курс доллара (ЦБ РФ): {rate}")
    else:
        print("Не удалось получить курс доллара с ЦБ РФ.")
    if rate_markup:
        print(f"Курс доллара с наценкой 2%: {rate_markup}")
    else:
        print("Не удалось получить курс с наценкой.") 