import os
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float, JSON
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime

# Используем переменные окружения для конфигурации подключения к PostgreSQL
DB_USER = os.getenv("POSTGRES_USER", "bot_user")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "bot_password")
DB_HOST = os.getenv("POSTGRES_HOST", "postgres") # Имя сервиса в docker-compose
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "telegram_bot")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
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

def init_db():
    """Инициализирует базу данных, создавая все необходимые таблицы."""
    print("Инициализация таблиц базы данных...")
    Base.metadata.create_all(bind=engine)
    print("Таблицы успешно созданы или уже существуют.")

def save_application(user_id: int, username: str, text: str):
    """Сохраняет новую заявку в базу данных с использованием SQLAlchemy."""
    db = SessionLocal()
    try:
        new_application = Application(
            user_id=user_id,
            username=username,
            application_text=text,
            timestamp=datetime.utcnow()
        )
        db.add(new_application)
        db.commit()
        db.refresh(new_application)
    finally:
        db.close() 