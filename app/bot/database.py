import sqlite3
from datetime import datetime

DB_NAME = 'applications.db'

def init_db():
    """Инициализирует базу данных и создает таблицу, если их нет."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            username TEXT,
            application_text TEXT NOT NULL,
            timestamp DATETIME NOT NULL
        )
    ''')
    conn.commit()
    conn.close()
    print("База данных успешно инициализирована.")

def save_application(user_id: int, username: str, text: str):
    """Сохраняет новую заявку в базу данных."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO applications (user_id, username, application_text, timestamp)
        VALUES (?, ?, ?, ?)
    ''', (user_id, username, text, datetime.now()))
    conn.commit()
    conn.close() 