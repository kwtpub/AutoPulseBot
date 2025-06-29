import os
import re
import asyncio
import ssl
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, JSON, text
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
ASYNC_DATABASE_URL = re.sub(r'^postgresql:', 'postgresql+asyncpg:', DATABASE_URL)
# Удаляем только sslmode=require (и &sslmode=require)
CLEAN_URL = re.sub(r'([&?])sslmode=require&?', r'\1', ASYNC_DATABASE_URL).rstrip('?&')

engine = create_async_engine(
    CLEAN_URL,
    echo=True,
    connect_args={"ssl": ssl.create_default_context()}
)
AsyncSessionLocal = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
Base = declarative_base()

class Application(Base):
    """Модель для хранения заявок от пользователей."""
    __tablename__ = 'applications'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    username = Column(String, nullable=True)
    application_text = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Application(user_id={self.user_id}, username='{self.username}')>"

class Car(Base):
    """Модель для каталога автомобилей."""
    __tablename__ = 'cars'
    id = Column(Integer, primary_key=True, index=True)
    
    # Уникальный ID, который мы генерируем и показываем в посте
    custom_id = Column(String, unique=True, index=True, nullable=False)
    
    # ID сообщения из канала-донора (для предотвращения дублей)
    source_message_id = Column(Integer, unique=True, index=True, nullable=False)
    
    # Юзернейм канала-донора
    source_channel_name = Column(String, index=True, nullable=False)
    
    # ID сообщения в нашем целевом канале (добавляется после публикации)
    target_channel_message_id = Column(Integer, unique=True, nullable=True)

    brand = Column(String, index=True)
    model = Column(String, index=True)
    year = Column(Integer, index=True)
    price = Column(Float, index=True)
    description = Column(Text)
    
    # Храним URL фотографий из Cloudinary
    photos = Column(JSON)  # Будет список URL-адресов
    
    status = Column(String, default='available', index=True)
    
    # Дата добавления в базу
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Car(custom_id='{self.custom_id}', brand='{self.brand}', model='{self.model}')>"

async def init_db():
    """Инициализирует базу данных, создавая все необходимые таблицы."""
    print("Инициализация таблиц базы данных...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Таблицы успешно созданы или уже существуют.")

async def save_application(user_id: int, username: str, text_: str):
    """Сохраняет новую заявку в базу данных с использованием SQLAlchemy."""
    async with AsyncSessionLocal() as session:
        new_application = Application(
            user_id=user_id,
            username=username,
            application_text=text_,
            timestamp=datetime.utcnow()
        )
        session.add(new_application)
        await session.commit()
        await session.refresh(new_application) 