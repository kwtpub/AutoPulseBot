import os
import aiohttp
import asyncio
import time
from dotenv import set_key, find_dotenv, load_dotenv

async def _get_new_iam_token(oauth_token):
    """Выполняет запрос к API Yandex для получения нового IAM-токена."""
    url = "https://iam.api.cloud.yandex.net/iam/v1/tokens"
    payload = {"yandexPassportOauthToken": oauth_token}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get("iamToken")
                else:
                    print(f"Ошибка при запросе IAM токена. Статус: {response.status}, Ответ: {await response.text()}")
                    return None
    except Exception as e:
        print(f"Исключение при запросе IAM токена: {e}")
        return None

async def check_and_refresh_iam_token():
    """
    Проверяет, не истек ли Yandex IAM токен, и обновляет его при необходимости.
    """
    load_dotenv()
    last_refresh_str = os.getenv("YANDEX_TOKEN_TIMESTAMP")
    
    needs_refresh = True
    if last_refresh_str:
        try:
            last_refresh_ts = int(last_refresh_str)
            # Токен живет 12 часов, обновляем через 11
            if time.time() - last_refresh_ts < 11 * 60 * 60:
                needs_refresh = False
                print("IAM токен еще действителен. Обновление не требуется.")
        except ValueError:
            print("Неверный формат YANDEX_TOKEN_TIMESTAMP. Будет произведено обновление.")

    if needs_refresh:
        print("IAM токен устарел или отсутствует. Запуск процедуры обновления...")
        oauth_token = os.getenv("YANDEX_OAUTH_TOKEN")
        if not oauth_token:
            print("Ошибка: YANDEX_OAUTH_TOKEN не найден в .env файле.")
            print("Пожалуйста, получите OAuth-токен и добавьте его в .env.")
            print("Инструкция: https://cloud.yandex.ru/docs/iam/concepts/authorization/oauth-token")
            return

        new_iam_token = await _get_new_iam_token(oauth_token)

        if new_iam_token:
            env_path = find_dotenv()
            if not env_path:
                print("Файл .env не найден. Создаю новый.")
                with open('.env', 'w') as f: pass
                env_path = find_dotenv()
            
            set_key(env_path, "YANDEX_IAM_TOKEN", new_iam_token)
            set_key(env_path, "YANDEX_TOKEN_TIMESTAMP", str(int(time.time())))
            os.environ['YANDEX_IAM_TOKEN'] = new_iam_token
            print("Yandex IAM токен успешно обновлен и сохранен в .env.")
        else:
            print("Не удалось обновить IAM токен.") 