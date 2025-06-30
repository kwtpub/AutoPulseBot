import os
from dotenv import load_dotenv
from telethon import TelegramClient

load_dotenv()
api_id = int(os.getenv("TELEGRAM_API_ID"))
api_hash = os.getenv("TELEGRAM_API_HASH")
session_name = "telegram_session"

client = TelegramClient(session_name, api_id, api_hash) 