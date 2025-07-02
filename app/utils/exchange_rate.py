import requests
from typing import Optional

API_URL = "https://bankiru-yakvenalex.amvera.io/api/v1/currency/usd"
API_BANK_URL = "https://bankiru-yakvenalex.amvera.io/api/v1/currency_by_bank/{bank_en}"


def get_usd_rate(bank: Optional[str] = None) -> Optional[float]:
    """
    Получает актуальный курс доллара США через API bankiru-yakvenalex.amvera.io
    
    Args:
        bank: Название банка (опционально, если не указано — берется средний курс по всем банкам)
    
    Returns:
        Курс доллара (float) или None при ошибке
    """
    try:
        if bank:
            # Для Сбербанка и других банков используем endpoint с английским названием
            bank_en = bank.lower()
            if bank_en == "сбербанк":
                bank_en = "sberbank"
            # Можно добавить другие маппинги при необходимости
            url = API_BANK_URL.format(bank_en=bank_en)
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            # Ищем USD в ответе
            for item in data.get("data", []):
                if item.get("currency_type", "").upper() == "USD":
                    return item.get("buy")
            return None
        else:
            # Старый способ — средний курс по всем банкам
            response = requests.get(API_URL, timeout=10)
            response.raise_for_status()
            data = response.json()
            rates = [item["buy"] for item in data["data"] if "buy" in item]
            if rates:
                return sum(rates) / len(rates)
            return None
    except Exception as e:
        print(f"Ошибка получения курса USD: {e}")
        return None

if __name__ == "__main__":
    rate = get_usd_rate("Сбербанк")
    if rate:
        print(f"Актуальный курс доллара (Сбербанк): {rate}")
    else:
        print("Не удалось получить курс доллара по Сбербанку.") 