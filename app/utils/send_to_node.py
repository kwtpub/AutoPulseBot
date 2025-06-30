import requests

def send_car_to_node(car_data, url="http://localhost:3001/api/cars"):
    """
    Отправляет данные о машине на Node.js сервер через HTTP POST.
    :param car_data: dict с данными автомобиля
    :param url: адрес Node.js сервера
    :return: dict с результатом или None
    """
    try:
        response = requests.post(url, json=car_data)
        response.raise_for_status()
        print("Машина добавлена:", response.json())
        return response.json()
    except Exception as e:
        print("Ошибка при добавлении:", e)
        return None

# Пример использования
if __name__ == "__main__":
    car = {
        "custom_id": "car-456",
        "source_message_id": 789,
        "source_channel_name": "@importdrive",
        "target_channel_message_id": None,
        "brand": "Honda",
        "model": "Civic",
        "year": 2018,
        "price": 15000,
        "description": "В отличном состоянии.",
        "photos": ["https://example.com/photo2.jpg"],
        "status": "available"
    }
    send_car_to_node(car) 