#!/usr/bin/env python3
"""
ReimDockify - Приложение для мониторинга Docker-контейнеров
Десктопное приложение в стиле Spotify для мониторинга Docker-контейнеров на Ubuntu.

Разработано в рамках университетского дипломного проекта, ReimDockify обеспечивает интуитивное
управление контейнерами, визуализацию метрик производительности и рекомендации по оптимизации
ресурсов для сред Docker на Ubuntu.

Функциональность:
- Мониторинг контейнеров в реальном времени (CPU, память, использование сети)
- Управление контейнерами (запуск, остановка, перезапуск, удаление)
- Настраиваемые оповещения при достижении пороговых значений ресурсов
- Просмотр кода для изучения файлов контейнера
- Визуализация метрик и создание отчетов
- Современный дизайн в стиле Spotify
- Аутентификация пользователей и хранение данных в базе данных

Использование:
    python main.py            # Обычный режим (требуется Docker)
    python main.py --demo     # Демо-режим (Docker не требуется)
    python main.py --help     # Показать справочную информацию

Зависимости:
    - customtkinter==5.2.0
    - docker==6.1.3
    - psutil==5.9.5
    - pandas==2.0.3
    - plotly==5.15.0
    - Pygments==2.15.1
    - psycopg2-binary==2.9.9
    - SQLAlchemy==2.0.23
    - alembic==1.12.1
    - bcrypt==4.0.1

Это основная точка входа в приложение.
"""
import os
import sys
import argparse
import logging
from typing import Optional
import tkinter as tk

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('reimdockify')

# Add the current directory to the path to import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Импортируем модуль с глобальными переменными
from utils.globals import set_disable_images

try:
    import customtkinter as ctk
    from ui.app import DockifyApp
    from ui.auth.login import LoginWindow
    from ui.auth.register import RegisterWindow
    from db.database import init_db
except ImportError as e:
    logger.error(f"Failed to import required modules: {e}")
    print("Error: Missing required dependencies. Please install them using:")
    print("pip install customtkinter==5.2.0 docker==6.1.3 psutil==5.9.5 "
          "pandas==2.0.3 plotly==5.15.0 Pygments==2.15.1 "
          "psycopg2-binary==2.9.9 SQLAlchemy==2.0.23 alembic==1.12.1 bcrypt==4.0.1")
    sys.exit(1)

def check_dependencies() -> bool:
    """Check if all required dependencies are installed."""
    try:
        import docker
        import psutil
        import pandas
        import plotly
        import pygments
        import sqlalchemy
        import psycopg2
        import bcrypt
        return True
    except ImportError as e:
        logger.error(f"Dependency check failed: {e}")
        return False

class DockifyLauncher:
    """
    Launcher for Dockify application with authentication flow.
    """
    def __init__(self, demo_mode: bool = False):
        """
        Initialize the launcher.
        
        Args:
            demo_mode: Whether to run in demo mode
        """
        self.demo_mode = demo_mode
        self.root = ctk.CTk()
        self.root.withdraw()  # Скрываем корневое окно
        
        # Set appearance mode and default color theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Инициализируем базу данных
        try:
            init_db(create_tables=True)
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            if not demo_mode:
                import tkinter.messagebox as messagebox
                messagebox.showerror(
                    "Database Error",
                    "Failed to connect to the database. The application will run in demo mode."
                )
                self.demo_mode = True
        
        # Показываем окно входа
        if demo_mode:
            # В демо-режиме сразу запускаем приложение
            self.start_app(user_id=0)
        else:
            # Показываем окно входа
            self.show_login()
    
    def show_login(self):
        """Show login window."""
        login_window = LoginWindow(
            self.root,
            on_login=self.start_app,
            on_register=self.show_register
        )
    
    def show_register(self):
        """Show registration window."""
        register_window = RegisterWindow(
            self.root,
            on_register=self.start_app,
            on_login=self.show_login
        )
    
    def start_app(self, user_id: int):
        """
        Start the main application.
        
        Args:
            user_id: User ID or 0 for demo mode
        """
        logger.info(f"Starting application for user_id={user_id}")
        
        # Если user_id == 0, это демо-режим
        if user_id == 0:
            self.demo_mode = True
            
        # Устанавливаем глобальную переменную для отключения изображений
        set_disable_images(False)
        
        # Закрываем корневое окно, чтобы избежать двух открытых окон
        self.root.destroy()
        
        # Инициализируем Docker клиент
        if self.demo_mode:
            # Импортируем здесь, чтобы избежать циклических импортов
            from core.mock_docker_client import MockDockerClient
            docker_client = MockDockerClient()
            logger.info("Created MockDockerClient for demo mode")
            
            # Создаем приложение с явным демо-режимом
            app = DockifyApp(docker_client=docker_client, force_demo=True, user_id=user_id)
        else:
            # Создаем приложение в обычном режиме
            app = DockifyApp(user_id=user_id)
        
        # Запускаем приложение
        app.mainloop()

def main() -> None:
    """Main function to initialize and run the application."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="ReimDockify - Приложение для мониторинга Docker-контейнеров")
    parser.add_argument("-d", "--demo", action="store_true", help="Запустить приложение в демонстрационном режиме с имитированными данными")
    parser.add_argument("-v", "--verbose", action="store_true", help="Включить подробный логирование (уровень DEBUG)")
    parser.add_argument("--init-db", action="store_true", help="Инициализировать базу данных и создать таблицы")
    args = parser.parse_args()
    
    # Set log level based on args
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Initialize database if requested
    if args.init_db:
        try:
            init_db(create_tables=True)
            logger.info("Database initialized successfully")
            return
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            sys.exit(1)
    
    # Launch the application
    launcher = DockifyLauncher(demo_mode=args.demo)
    
    # Run the app
    try:
        launcher.root.mainloop()
    except Exception as e:
        logger.error(f"Application crashed: {e}")
        raise

if __name__ == "__main__":
    main()
