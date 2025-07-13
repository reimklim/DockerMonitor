#!/usr/bin/env python3
"""
Скрипт для инициализации базы данных и создания тестового пользователя.
"""
import os
import sys
import logging
import argparse

# Добавляем корневую директорию проекта в путь поиска модулей
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.database import init_db, get_db_session
from db.services.user_service import UserService

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('dockify.init_db')

def create_test_user(username: str, email: str, password: str, is_admin: bool = False):
    """
    Создать тестового пользователя.
    
    Args:
        username: Имя пользователя
        email: Email пользователя
        password: Пароль
        is_admin: Флаг администратора
    """
    try:
        # Получаем сессию базы данных
        db_session = get_db_session()
        
        # Создаем сервис для работы с пользователями
        user_service = UserService(db_session)
        
        # Проверяем, существует ли пользователь с таким именем
        existing_user = user_service.get_user_by_username(username)
        if existing_user:
            logger.info(f"User {username} already exists with ID {existing_user.id}")
            return
        
        # Создаем пользователя
        user = user_service.create_user(
            username=username,
            email=email,
            password=password,
            full_name=f"{username.capitalize()} User",
            is_admin=is_admin
        )
        
        if user:
            logger.info(f"User {username} created successfully with ID {user.id}")
        else:
            logger.error(f"Failed to create user {username}")
    except Exception as e:
        logger.error(f"Error creating test user: {e}")
        raise

def main():
    """Основная функция скрипта."""
    parser = argparse.ArgumentParser(description="Initialize database and create test users")
    parser.add_argument("--create-tables", action="store_true", help="Create database tables")
    parser.add_argument("--create-users", action="store_true", help="Create test users")
    parser.add_argument("--username", type=str, default="admin", help="Username for test user")
    parser.add_argument("--email", type=str, default="admin@example.com", help="Email for test user")
    parser.add_argument("--password", type=str, default="password", help="Password for test user")
    parser.add_argument("--admin", action="store_true", help="Make the user an admin")
    
    args = parser.parse_args()
    
    try:
        # Инициализируем базу данных
        init_db(create_tables=args.create_tables)
        logger.info("Database initialized successfully")
        
        # Создаем тестового пользователя, если указан флаг
        if args.create_users:
            create_test_user(
                username=args.username,
                email=args.email,
                password=args.password,
                is_admin=args.admin
            )
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 