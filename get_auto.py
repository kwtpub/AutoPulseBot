#!/usr/bin/env python3
"""
Утилита для получения данных автомобиля по custom_id
Использование: python get_auto.py <custom_id> <user_id>
"""
import sys
import os
import asyncio
import aiohttp
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.sessions import StringSession
from io import BytesIO

load_dotenv()

# Настройки Telegram
api_id = int(os.getenv("TELEGRAM_API_ID"))
api_hash = os.getenv("TELEGRAM_API_HASH")
session_string = os.getenv("TELEGRAM_SESSION_STRING", "")

if not session_string:
    print("❌ TELEGRAM_SESSION_STRING не найден в .env файле")
    print("Запустите: python generate_session.py")
    sys.exit(1)

# Настройки Node.js API
NODE_API_URL = f"http://localhost:{os.getenv('NODE_PORT', 3001)}/api"

async def get_car_from_api(custom_id: str):
    """Получает данные автомобиля из Node.js API"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{NODE_API_URL}/cars/{custom_id}") as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 404:
                    return None
                else:
                    error_text = await response.text()
                    print(f"❌ Ошибка API: {response.status} - {error_text}")
                    return None
    except Exception as e:
        print(f"❌ Ошибка подключения к API: {e}")
        return None

async def download_image(url: str) -> BytesIO:
    """Скачивает изображение по URL и возвращает BytesIO объект"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    image_data = await response.read()
                    return BytesIO(image_data)
                else:
                    print(f"⚠️  Не удалось скачать изображение: {url}")
                    return None
    except Exception as e:
        print(f"⚠️  Ошибка скачивания изображения {url}: {e}")
        return None

def format_car_message(car_data: dict) -> str:
    """Форматирует информацию об автомобиле для отправки"""
    message = f"🚗 **Информация об автомобиле**\n\n"
    
    # Основная информация
    if car_data.get('brand') and car_data.get('model'):
        message += f"**{car_data['brand']} {car_data['model']}**"
        if car_data.get('year'):
            message += f" ({car_data['year']})"
        message += "\n\n"
    
    # Цена
    if car_data.get('price'):
        try:
            price = float(car_data['price'])
            message += f"💰 **Цена:** {price:,.0f} ₽\n\n"
        except:
            message += f"💰 **Цена:** {car_data['price']}\n\n"
    
    # Описание
    if car_data.get('description'):
        # Убираем ID из начала описания для чистоты
        description = car_data['description']
        if description.startswith('ID:'):
            lines = description.split('\n')
            description = '\n'.join(lines[1:]).strip()
        message += f"📝 **Описание:**\n{description}\n\n"
    
    # Техническая информация
    message += f"🆔 **ID:** {car_data.get('custom_id', 'N/A')}\n"
    
    if car_data.get('source_channel_name'):
        message += f"📺 **Источник:** {car_data['source_channel_name']}\n"
    
    if car_data.get('status'):
        status_emoji = {
            'available': '✅',
            'sold': '❌', 
            'reserved': '⏳',
            'error': '⚠️'
        }
        emoji = status_emoji.get(car_data['status'], '❓')
        message += f"{emoji} **Статус:** {car_data['status']}\n"
    
    if car_data.get('created_at'):
        message += f"📅 **Добавлено:** {car_data['created_at'][:10]}\n"
    
    message += "\n📞 **Контакт:** @VroomMarketManager"
    
    return message

async def send_car_to_user(custom_id: str, user_id: int):
    """Отправляет информацию об автомобиле пользователю в ЛС"""
    print(f"🔍 Поиск автомобиля с ID: {custom_id}")
    
    # Получаем данные из API
    car_data = await get_car_from_api(custom_id)
    
    if not car_data:
        print(f"❌ Автомобиль с ID {custom_id} не найден")
        return False
    
    print(f"✅ Автомобиль найден: {car_data.get('brand', 'N/A')} {car_data.get('model', 'N/A')}")
    
    # Подключаемся к Telegram
    client = TelegramClient(StringSession(session_string), api_id, api_hash)
    
    try:
        await client.start()
        print("✅ Подключение к Telegram установлено")
        
        # Форматируем сообщение
        message = format_car_message(car_data)
        
        # Получаем фотографии
        photos = car_data.get('photos', [])
        
        if photos and len(photos) > 0:
            print(f"📸 Скачивание {len(photos)} фотографий...")
            
            # Скачиваем фотографии
            photo_files = []
            for i, photo_url in enumerate(photos[:10], 1):  # Максимум 10 фото
                print(f"  📥 Скачивание фото {i}/{len(photos)}...")
                photo_data = await download_image(photo_url)
                if photo_data:
                    photo_files.append(photo_data)
                # Небольшая задержка между скачиваниями
                if i < len(photos) and len(photos) > 1:
                    await asyncio.sleep(0.5)
            
            if photo_files:
                print(f"📤 Отправка сообщения с {len(photo_files)} фотографиями...")
                
                # Отправляем фотографии с подписью
                try:
                    await client.send_file(
                        user_id, 
                        photo_files, 
                        caption=message
                    )
                except Exception as e:
                    if "wait" in str(e).lower() and "seconds" in str(e).lower():
                        print(f"⚠️  Telegram флуд-лимит: {e}")
                        print("📤 Пробуем отправить только первое фото...")
                        try:
                            # Пробуем отправить только первое фото
                            await client.send_file(
                                user_id, 
                                photo_files[0], 
                                caption=f"{message}\n\n⚠️ Остальные фото временно недоступны из-за ограничений Telegram"
                            )
                        except:
                            print("📤 Отправляем только текст без фотографий...")
                            await client.send_message(
                                user_id,
                                f"⚠️ Фотографии временно недоступны из-за ограничений Telegram\n\n{message}"
                            )
                    else:
                        raise e
            else:
                # Если фото не удалось скачать, отправляем только текст
                print("⚠️  Не удалось скачать фотографии, отправляем только текст")
                await client.send_message(user_id, message)
        else:
            # Нет фотографий, отправляем только текст
            print("📤 Отправка текстового сообщения...")
            await client.send_message(user_id, message)
        
        # Отправляем отдельное сообщение с кнопкой для связи с менеджером
        from telethon.tl.types import KeyboardButtonUrl
        from telethon.tl.types import ReplyInlineMarkup
        
        # Создаем URL с pre-filled сообщением
        pre_filled_text = f"Меня заинтересовало авто под ID {custom_id}"
        manager_url = f"https://t.me/VroomMarketManager?text={pre_filled_text.replace(' ', '%20')}"
        
        contact_button = KeyboardButtonUrl(
            text="📞 Написать менеджеру",
            url=manager_url
        )
        
        keyboard = ReplyInlineMarkup([
            [contact_button]
        ])
        
        contact_message = (
            "💬 **Заинтересовало это авто?**\n\n"
            "Свяжитесь с нашим менеджером для получения дополнительной информации "
            "и организации просмотра автомобиля."
        )
        
        print("📤 Отправка сообщения с кнопкой менеджера...")
        await client.send_message(
            user_id,
            contact_message,
            buttons=keyboard
        )
        
        print(f"✅ Информация об автомобиле {custom_id} отправлена пользователю {user_id}")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка отправки сообщения: {e}")
        return False
    finally:
        await client.disconnect()

async def main():
    """Главная функция"""
    if len(sys.argv) != 3:
        print("❌ Неправильное использование!")
        print("Использование: python get_auto.py <custom_id> <user_id>")
        print("Пример: python get_auto.py 12345678 987654321")
        sys.exit(1)
    
    custom_id = sys.argv[1]
    try:
        user_id = int(sys.argv[2])
    except ValueError:
        print("❌ user_id должен быть числом!")
        sys.exit(1)
    
    print(f"🚀 Запуск утилиты get_auto")
    print(f"🆔 Custom ID: {custom_id}")
    print(f"👤 User ID: {user_id}")
    print()
    
    # Проверяем доступность API
    print("🔍 Проверка доступности Node.js API...")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{NODE_API_URL}/health") as response:
                if response.status == 200:
                    print("✅ Node.js API доступен")
                else:
                    print(f"⚠️  Node.js API вернул статус {response.status}")
    except Exception as e:
        print(f"❌ Node.js API недоступен: {e}")
        print("Убедитесь что сервер запущен: node app/db/server.js")
        sys.exit(1)
    
    # Отправляем данные пользователю
    success = await send_car_to_user(custom_id, user_id)
    
    if success:
        print("\n🎉 Операция завершена успешно!")
    else:
        print("\n❌ Операция завершена с ошибкой!")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 