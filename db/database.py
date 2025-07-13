"""
Модуль для работы с базой данных PostgreSQL.
"""
import os
import logging
from typing import Optional
from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base

logger = logging.getLogger('dockify.db')

# Базовый класс для всех моделей
Base = declarative_base()

# Настройки подключения к базе данных
DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_PORT = os.environ.get('DB_PORT', '5432')
DB_NAME = os.environ.get('DB_NAME', 'dockify')
DB_USER = os.environ.get('DB_USER', os.environ.get('USER', 'postgres'))
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'KklimK2003')

# URL для подключения к базе данных
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
# Если пароль пустой, используем другой формат URL
if not DB_PASSWORD:
    DATABASE_URL = f"postgresql://{DB_USER}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Глобальный экземпляр движка SQLAlchemy
engine: Optional[Engine] = None

# Фабрика сессий
SessionLocal = None


def get_engine() -> Engine:
    """
    Получить экземпляр движка SQLAlchemy.
    
    Returns:
        Engine: Экземпляр движка SQLAlchemy
    """
    global engine
    if engine is None:
        try:
            engine = create_engine(
                DATABASE_URL,
                echo=False,  # Отключаем вывод SQL-запросов в лог
                pool_pre_ping=True,  # Проверка соединения перед использованием
                pool_recycle=3600,  # Пересоздание соединения через час
            )
            logger.info(f"Successfully connected to database at {DB_HOST}:{DB_PORT}/{DB_NAME}")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    return engine


def get_session_factory():
    """
    Получить фабрику сессий SQLAlchemy.
    
    Returns:
        sessionmaker: Фабрика сессий SQLAlchemy
    """
    global SessionLocal
    if SessionLocal is None:
        engine = get_engine()
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal


def get_db_session() -> Session:
    """
    Получить сессию базы данных.
    
    Returns:
        Session: Сессия SQLAlchemy
    """
    session_factory = get_session_factory()
    session = session_factory()
    try:
        return session
    except Exception as e:
        session.close()
        logger.error(f"Error getting database session: {e}")
        raise


def init_db(create_tables: bool = False) -> None:
    """
    Инициализировать базу данных.
    
    Args:
        create_tables: Создать таблицы в базе данных
    """
    try:
        engine = get_engine()
        if create_tables:
            # Импортируем все модели, чтобы они были зарегистрированы в Base.metadata
            from db.models.user import User
            from db.models.container_history import ContainerHistory
            from db.models.alert_history import AlertHistory
            from db.models.user_settings import UserSettings
            from db.models.report import Report
            
            # Создаем все таблицы
            Base.metadata.create_all(bind=engine)
            logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise 