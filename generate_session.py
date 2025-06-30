#!/usr/bin/env python3
"""
Скрипт для генерации StringSession для Telethon
Запустите этот скрипт один раз, чтобы получить строковую сессию
"""
import os
import asyncio
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.sessions import StringSession

load_dotenv()

api_id = int(os.getenv("TELEGRAM_API_ID"))
api_hash = os.getenv("TELEGRAM_API_HASH")
phone = os.getenv("TELEGRAM_PHONE")

async def generate_session():
    """Генерирует StringSession для Telethon"""
    print("Генерация StringSession для Telethon...")
    
    # Используем StringSession вместо файловой сессии
    client = TelegramClient(StringSession(), api_id, api_hash)
    
    try:
        await client.start(phone=phone)
        print("Авторизация успешна!")
        
        # Получаем строковую сессию
        session_string = client.session.save()
        
        print("\n" + "="*50)
        print("TELEGRAM_SESSION_STRING:")
        print(session_string)
        print("="*50)
        print("\nДобавьте эту строку в ваш .env файл как:")
        print(f"TELEGRAM_SESSION_STRING={session_string}")
        print("\nПосле этого можете удалить файлы *.session")
        
    except Exception as e:
        print(f"Ошибка при генерации сессии: {e}")
    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(generate_session()) 