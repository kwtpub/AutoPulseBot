import os
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.sessions import StringSession

load_dotenv()

api_id = int(os.getenv("TELEGRAM_API_ID"))
api_hash = os.getenv("TELEGRAM_API_HASH")
session_string = os.getenv("TELEGRAM_SESSION_STRING", "")

if not session_string:
    raise ValueError(
        "TELEGRAM_SESSION_STRING not found in environment variables. "
        "Please run 'python generate_session.py' to generate it."
    )

# Используем StringSession вместо файловой сессии
client = TelegramClient(StringSession(session_string), api_id, api_hash) 