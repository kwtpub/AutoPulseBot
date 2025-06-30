import cloudinary
import cloudinary.uploader
import os

# Загружаем CLOUDINARY_URL из переменных окружения
CLOUDINARY_URL = os.getenv("CLOUDINARY_URL")

if not CLOUDINARY_URL:
    print("Предупреждение: CLOUDINARY_URL не установлен. Загрузка в Cloudinary не будет работать.")
    # Можно установить значения по умолчанию или заглушки, если это необходимо для локального тестирования без Cloudinary
    cloudinary.config(
        cloud_name = "test_cloud",
        api_key = "test_key",
        api_secret = "test_secret",
        secure = True
    )
else:
    # Конфигурируем Cloudinary с использованием URL
    cloudinary.config(cloudinary_url=CLOUDINARY_URL, secure=True)

def upload_image_to_cloudinary(image_path: str, public_id: str = None) -> dict:
    """
    Загружает изображение в Cloudinary.

    :param image_path: Путь к локальному файлу изображения.
    :param public_id: (Опционально) Уникальный идентификатор для файла в Cloudinary.
                      Если не указан, Cloudinary сгенерирует его автоматически.
    :return: Словарь с информацией о загруженном изображении от Cloudinary.
             Возвращает None в случае ошибки.
    """
    if not CLOUDINARY_URL and not os.getenv("CLOUDINARY_CLOUD_NAME"): # Проверяем, если есть хотя бы какая-то конфигурация
        print("Ошибка: Cloudinary не сконфигурирован. Загрузка невозможна.")
        return None

    try:
        upload_options = {}
        if public_id:
            upload_options["public_id"] = public_id
            upload_options["overwrite"] = True # Перезаписывать, если файл с таким public_id уже существует

        result = cloudinary.uploader.upload(image_path, **upload_options)
        print(f"Изображение {image_path} успешно загружено в Cloudinary. URL: {result.get('secure_url')}")
        return result
    except Exception as e:
        print(f"Ошибка при загрузке изображения {image_path} в Cloudinary: {e}")
        return None

def get_image_url_from_cloudinary(public_id: str, transformations: dict = None) -> str:
    """
    Получает URL изображения из Cloudinary с возможностью применения трансформаций.

    :param public_id: Уникальный идентификатор файла в Cloudinary.
    :param transformations: (Опционально) Словарь с параметрами трансформации
                              (например, {'width': 150, 'height': 150, 'crop': 'fill'}).
    :return: URL изображения или None, если public_id не найден или Cloudinary не сконфигурирован.
    """
    if not CLOUDINARY_URL and not os.getenv("CLOUDINARY_CLOUD_NAME"):
        print("Ошибка: Cloudinary не сконфигурирован. Получение URL невозможно.")
        return None

    try:
        if transformations:
            url = cloudinary.CloudinaryImage(public_id).build_url(transformation=transformations)
        else:
            url = cloudinary.CloudinaryImage(public_id).build_url()
        return url
    except Exception as e:
        print(f"Ошибка при получении URL для public_id {public_id} из Cloudinary: {e}")
        return None

def get_car_photos_urls(custom_id: str, count: int = 10) -> list:
    """
    Получает список URL-ов всех фотографий автомобиля из Cloudinary по custom_id.
    
    :param custom_id: Уникальный ID автомобиля
    :param count: Максимальное количество фотографий для поиска (по умолчанию 10)
    :return: Список URL-ов фотографий
    """
    if not CLOUDINARY_URL and not os.getenv("CLOUDINARY_CLOUD_NAME"):
        print("Ошибка: Cloudinary не сконфигурирован. Получение URL невозможно.")
        return []
    
    photo_urls = []
    for i in range(1, count + 1):
        public_id = f"car_{custom_id}_{i}"
        try:
            # Проверяем существование изображения и получаем URL
            url = cloudinary.CloudinaryImage(public_id).build_url()
            if url:
                photo_urls.append(url)
        except Exception as e:
            # Если фото с таким public_id не найдено, прекращаем поиск
            break
    
    return photo_urls

def get_car_photo_thumbnails(custom_id: str, count: int = 10, width: int = 300, height: int = 200) -> list:
    """
    Получает список URL-ов миниатюр всех фотографий автомобиля из Cloudinary.
    
    :param custom_id: Уникальный ID автомобиля
    :param count: Максимальное количество фотографий для поиска
    :param width: Ширина миниатюры
    :param height: Высота миниатюры
    :return: Список URL-ов миниатюр
    """
    if not CLOUDINARY_URL and not os.getenv("CLOUDINARY_CLOUD_NAME"):
        print("Ошибка: Cloudinary не сконфигурирован. Получение URL невозможно.")
        return []
    
    thumbnail_urls = []
    for i in range(1, count + 1):
        public_id = f"car_{custom_id}_{i}"
        try:
            # Создаем миниатюру с трансформацией
            url = cloudinary.CloudinaryImage(public_id).build_url(
                transformation={'width': width, 'height': height, 'crop': 'fill'}
            )
            if url:
                thumbnail_urls.append(url)
        except Exception as e:
            # Если фото с таким public_id не найдено, прекращаем поиск
            break
    
    return thumbnail_urls

if __name__ == '__main__':
    # Пример использования (для этого нужно иметь файл test.jpg в корне проекта или указать другой путь)
    # и установленный CLOUDINARY_URL в переменных окружения

    # Создадим фейковый файл для теста, если CLOUDINARY_URL не установлен, чтобы не было ошибки
    if not CLOUDINARY_URL and not os.path.exists("test.jpg"):
        try:
            from PIL import Image
            img = Image.new('RGB', (60, 30), color = 'red')
            img.save('test.jpg')
            print("Создан тестовый файл test.jpg")
        except ImportError:
            print("PIL не установлен, не могу создать тестовый файл. Пропустим тест загрузки.")
            exit()
        except Exception as e:
            print(f"Не удалось создать тестовый файл: {e}")
            exit()


    if CLOUDINARY_URL or os.getenv("CLOUDINARY_CLOUD_NAME"): # Только если есть конфигурация
        test_image_path = "test.jpg"
        if os.path.exists(test_image_path):
            # 1. Загрузка изображения
            upload_result = upload_image_to_cloudinary(test_image_path, public_id="test_car_image")

            if upload_result:
                print(f"Результат загрузки: {upload_result}")
                uploaded_public_id = upload_result.get("public_id")

                # 2. Получение URL загруженного изображения
                image_url = get_image_url_from_cloudinary(uploaded_public_id)
                if image_url:
                    print(f"URL изображения: {image_url}")

                # 3. Получение URL с трансформациями
                transformed_image_url = get_image_url_from_cloudinary(
                    uploaded_public_id,
                    transformations={'width': 100, 'height': 100, 'crop': 'thumb'}
                )
                if transformed_image_url:
                    print(f"URL трансформированного изображения: {transformed_image_url}")
            else:
                print("Загрузка тестового изображения не удалась.")
        else:
            print(f"Тестовый файл {test_image_path} не найден. Пропустим тест загрузки и получения URL.")
    else:
        print("CLOUDINARY_URL не установлен. Пропустим тест взаимодействия с Cloudinary.")

    # Очистка тестового файла
    # if not CLOUDINARY_URL and os.path.exists("test.jpg"):
    #     try:
    #         os.remove("test.jpg")
    #         print("Тестовый файл test.jpg удален.")
    #     except Exception as e:
    #         print(f"Не удалось удалить тестовый файл: {e}")
