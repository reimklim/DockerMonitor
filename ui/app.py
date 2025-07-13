"""
Main application window and UI controller for Dockify.
"""
import os
import sys
import time
import logging
from typing import Dict, List, Any, Optional, Callable
import threading
import tkinter as tk
from tkinter import messagebox

import customtkinter as ctk

from core.docker_client import DockerClient
from typing import Union, TYPE_CHECKING

# Импортируем MockDockerClient только при необходимости
from core.mock_docker_client import MockDockerClient
from core.monitor import ContainerMonitor
from core.alerts import AlertManager
from ui.overview import OverviewFrame
from ui.containers import ContainersFrame
from ui.metrics import MetricsFrame
from ui.reports import ReportsFrame
from ui.code_explorer import CodeExplorerFrame
from ui.sidebar import SidebarFrame
from ui.components import AlertNotification
from utils.theme import apply_theme, SPOTIFY_COLORS
from utils.config import AppConfig
from assets.icons import get_icon_image
from ui.settings import SettingsDialog

from db.database import get_db_session
from db.services.user_service import UserService
from db.services.settings_service import SettingsService
from db.services.metrics_service import MetricsService

logger = logging.getLogger('reimdockify.app')

class DockifyApp(ctk.CTk):
    """
    Main application window for Dockify.
    """
    def __init__(self, docker_client=None, force_demo=False, user_id: int = 0):
        # Type hints for IDE
        if TYPE_CHECKING:
            from core.mock_docker_client import MockDockerClient
            self.docker_client: Union[DockerClient, "MockDockerClient"]
        """Initialize the application window and components.
        
        Args:
            docker_client: Optional pre-initialized Docker client
            force_demo: Force demo mode regardless of Docker connectivity
            user_id: ID пользователя (0 для демо-режима)
        """
        super().__init__()
                
        # Setup window
        self.title("ReimDockify - Монитор Docker-контейнеров")
        self.geometry("1500x900")
        self.minsize(1000, 700)
        
        # Сохраняем ID пользователя
        self.user_id = user_id
        
        # Инициализируем сервисы для работы с БД
        if user_id > 0:
            try:
                self.db_session = get_db_session()
                self.user_service = UserService(self.db_session)
                self.settings_service = SettingsService(self.db_session)
                self.metrics_service = MetricsService(self.db_session)
                
                # Получаем пользователя
                self.user = self.user_service.get_user_by_id(user_id)
                if not self.user:
                    logger.error(f"User with ID {user_id} not found")
                    messagebox.showerror(
                        "User Error",
                        f"User with ID {user_id} not found. The application will exit."
                    )
                    sys.exit(1)
                
                # Получаем настройки пользователя
                self.user_settings = self.settings_service.get_settings_dict(user_id)
                logger.info(f"Loaded settings for user {self.user.username}")
                
                # Устанавливаем заголовок с именем пользователя
                self.title(f"ReimDockify - Монитор Docker-контейнеров - {self.user.username}")
            except Exception as e:
                logger.error(f"Failed to initialize database services: {e}")
                messagebox.showerror(
                    "Database Error",
                    "Failed to connect to the database. The application will exit."
                )
                sys.exit(1)
        else:
            # Демо-режим
            self.user = None
            self.user_settings = {
                'poll_interval': 5,
                'docker_socket': '/var/run/docker.sock',
                'enable_alerts': True,
                'auto_adjust_interval': True,
                'theme': 'dark'
            }
        
        # Load config
        self.config = AppConfig()
        
        # Application flags
        self.demo_mode = force_demo or user_id == 0
        
        # Инициализация флага для уведомлений
        self.enable_alerts = self.user_settings.get('enable_alerts', True)
        
        # Apply theme
        apply_theme(self)
        
        # Initialize core components
        try:
            # Use the provided Docker client if available
            if docker_client is not None:
                self.docker_client = docker_client
                logger.info("Using pre-initialized Docker client")
            # In demo mode, use MockDockerClient
            elif self.demo_mode:
                self.docker_client = MockDockerClient()
                logger.info("Created MockDockerClient for demo mode")
            # Otherwise try to connect to Docker
            else:
                try:
                    # Используем путь к сокету из настроек пользователя
                    socket_path = self.user_settings.get('docker_socket', '/var/run/docker.sock')
                    self.docker_client = DockerClient(socket_path=socket_path)
                    logger.info(f"Successfully connected to Docker daemon using socket {socket_path}")
                    
                    # Verify that Docker is working by checking containers
                    try:
                        containers = self.docker_client.list_containers()
                        
                        # Even if Docker is running but there are no containers or errors in conversion
                        # Suggest demo mode as well
                        if not containers:
                            logger.warning("No Docker containers found. Offering demo mode.")
                            result = messagebox.askyesno(
                                "Контейнеры Docker не найдены",
                                "Docker запущен, но контейнеры не найдены.\n\n"
                                "Хотите запустить приложение в демо-режиме с симулированными контейнерами?"
                            )
                            if result:  # Yes, use demo mode
                                self.docker_client = MockDockerClient()
                                self.demo_mode = True
                                logger.info("Switched to demo mode by user choice (no containers)")
                            # Otherwise continue with empty Docker
                    except Exception as container_err:
                        logger.error(f"Failed to get Docker containers: {container_err}")
                        result = messagebox.askyesno(
                            "Ошибка контейнеров Docker",
                            f"Ошибка при доступе к контейнерам Docker:\n\n{str(container_err)}\n\n"
                            "Хотите запустить приложение в демо-режиме с симулированными контейнерами?"
                        )
                        if result:  # Yes, use demo mode
                            self.docker_client = MockDockerClient()
                            self.demo_mode = True
                            logger.info("Switched to demo mode due to container access error")
                        
                except Exception as docker_err:
                    logger.error(f"Failed to connect to Docker daemon: {docker_err}")
                    result = messagebox.askretrycancel(
                        "Ошибка подключения к Docker",
                        f"Не удалось подключиться к Docker:\n\n{str(docker_err)}\n\n"
                        "Убедитесь, что Docker запущен и у вас есть права доступа к нему.\n\n"
                        "Нажмите 'Повторить' для повторной попытки или 'Отмена' для запуска в демо-режиме."
                    )
                    if result:  # Retry
                        try:
                            self.docker_client = DockerClient()
                            logger.info("Successfully connected to Docker daemon on retry")
                            self.demo_mode = False
                        except Exception as retry_err:
                            logger.error(f"Failed to connect to Docker daemon on retry: {retry_err}")
                            messagebox.showinfo(
                                "Демо режим активирован",
                                "Не удалось подключиться к Docker. Приложение будет запущено в демо-режиме с симулированными данными."
                            )
                            self.demo_mode = True
                            # Create a mock Docker client for demo mode
                            self.docker_client = MockDockerClient()
                    else:  # Cancel = use demo mode
                        logger.info("User chose demo mode after Docker connection error")
                        self.demo_mode = True
                        self.docker_client = MockDockerClient()
                
            # Set window title based on mode
            if self.demo_mode:
                if self.user:
                    self.title(f"ReimDockify - Монитор Docker-контейнеров [ДЕМО РЕЖИМ] - {self.user.username}")
                else:
                    self.title("ReimDockify - Монитор Docker-контейнеров [ДЕМО РЕЖИМ]")
            
            # Initialize monitoring components
            poll_interval = self.user_settings.get('poll_interval', 5)
            self.container_monitor = ContainerMonitor(self.docker_client, refresh_interval=poll_interval)
            self.alert_manager = AlertManager()
            
        except Exception as e:
            logger.error(f"Failed to initialize core components: {e}")
            messagebox.showerror("Initialization Error", 
                                f"Failed to initialize application components:\n{str(e)}")
            sys.exit(1)
        
        # Setup callbacks
        self.container_monitor.add_callback(self.on_metrics_update)
        self.alert_manager.add_callback(self.on_new_alerts)
        
        # Create UI
        self.create_ui()
        
        # Start monitoring
        self.container_monitor.start_monitoring()
        
        # Setup protocol for window close
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        
    def create_ui(self):
        """Create and setup the user interface."""
        # Create main container
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Create sidebar
        self.sidebar = SidebarFrame(self)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        # Create content frames
        self.overview_frame = OverviewFrame(self, self.docker_client, 
                                          self.container_monitor, self.alert_manager)
        self.containers_frame = ContainersFrame(self, self.docker_client)
        self.metrics_frame = MetricsFrame(self, self.docker_client, 
                                         self.container_monitor)
        self.reports_frame = ReportsFrame(self, self.docker_client, 
                                         self.container_monitor)
        # Code Explorer
        import pathlib
        proj_root = pathlib.Path(__file__).parent.parent  # на уровень вверх от ui/
        self.code_explorer_frame = CodeExplorerFrame(self, str(proj_root))
        
        # Place overview frame initially
        self.overview_frame.grid(row=0, column=1, sticky="nsew")
        self.active_frame = self.overview_frame
        
        # Setup sidebar buttons
        self.sidebar.btn_overview.configure(command=lambda: self.show_frame(self.overview_frame))
        self.sidebar.btn_containers.configure(command=lambda: self.show_frame(self.containers_frame))
        self.sidebar.btn_metrics.configure(command=lambda: self.show_frame(self.metrics_frame))
        self.sidebar.btn_reports.configure(command=lambda: self.show_frame(self.reports_frame))
        self.sidebar.btn_code.configure(command=lambda: self.show_frame(self.code_explorer_frame))
        self.sidebar.btn_settings.configure(command=self.open_settings)
        
        # Setup logout button
        self.sidebar.btn_logout.configure(command=self.logout)
        
        # Set overview as active button initially
        self.sidebar.set_active(self.sidebar.btn_overview)
        
        # Alert notification container
        self.notifications_frame = ctk.CTkFrame(self, fg_color="transparent")
        # Use a smaller relative width and height, and make it only visible when actually needed
        self.notifications_frame.place(relx=1.0, rely=0.0, anchor="ne", 
                                     x=-20, y=20, relwidth=0.25, relheight=0.2)
        # Hide it by default until there are actual notifications
        self.notifications_frame.lower()  # Send it to the back initially
        self.notifications = []
        
    def show_frame(self, frame):
        """
        Switch between content frames.
        
        Args:
            frame: The frame to show
        """
        if self.active_frame:
            self.active_frame.grid_forget()
        
        frame.grid(row=0, column=1, sticky="nsew")
        self.active_frame = frame
        
        # Update sidebar button highlighting
        if frame == self.overview_frame:
            self.sidebar.set_active(self.sidebar.btn_overview)
        elif frame == self.containers_frame:
            self.sidebar.set_active(self.sidebar.btn_containers)
        elif frame == self.metrics_frame:
            self.sidebar.set_active(self.sidebar.btn_metrics)
        elif frame == self.reports_frame:
            self.sidebar.set_active(self.sidebar.btn_reports)
        elif frame == self.code_explorer_frame:
            self.sidebar.set_active(self.sidebar.btn_code)
        
        # Update the frame's content if it has a refresh method
        if hasattr(frame, 'refresh'):
            frame.refresh()
    
    def on_metrics_update(self, metrics: Dict[str, Dict[str, Any]]):
        """
        Callback when new metrics are collected.
        
        Args:
            metrics: Dictionary of container metrics
        """
        # Сохраняем метрики в базу данных, если это не демо-режим
        if not self.demo_mode and self.user_id > 0:
            try:
                self.metrics_service.save_metrics(self.user_id, metrics)
            except Exception as e:
                logger.error(f"Failed to save metrics to database: {e}")
        
        # Pass metrics to alert manager for threshold checking
        self.alert_manager.check_alerts(metrics)
        
        # Update UI if needed
        if self.active_frame == self.overview_frame:
            self.overview_frame.update_metrics(metrics)
        elif self.active_frame == self.containers_frame:
            self.containers_frame.update_metrics(metrics)
        elif self.active_frame == self.metrics_frame:
            self.metrics_frame.update_metrics(metrics)
    
    def on_new_alerts(self, alerts: List[Dict[str, Any]]):
        """
        Callback when new alerts are generated.
        
        Args:
            alerts: List of new alert dictionaries
        """
        # Проверяем, включены ли уведомления
        if not hasattr(self, 'enable_alerts'):
            self.enable_alerts = True  # По умолчанию уведомления включены
            
        if alerts and self.enable_alerts:
            # Make notification frame visible when there are alerts
            self.notifications_frame.lift()  # Bring to the front
            
            # Show notifications for each alert
            for alert in alerts:
                self.show_notification(alert)
    
    def show_notification(self, alert: Dict[str, Any]):
        """
        Show an alert notification.
        
        Args:
            alert: Alert dictionary
        """
        # Create new notification
        notification = AlertNotification(self.notifications_frame, alert)
        
        # Position vertically based on existing notifications
        y_pos = 0
        for existing in self.notifications:
            if not existing.winfo_exists():
                self.notifications.remove(existing)
                continue
            y_pos += existing.winfo_height() + 10
                
        notification.place(x=0, y=y_pos, relwidth=1.0)
        self.notifications.append(notification)
        
        # Schedule notification to fade out and be removed after 5 seconds
        self.after(5000, lambda n=notification: self.fade_out_notification(n))
        
    def fade_out_notification(self, notification):
        """
        Fade out and remove a notification.
        
        Args:
            notification: Notification widget to remove
        """
        notification.fade_out(callback=lambda: self.remove_notification(notification))
        
    def remove_notification(self, notification):
        """
        Remove a notification from the UI.
        
        Args:
            notification: Notification widget to remove
        """
        # убираем уведомление из списка и удаляем виджет
        if notification in self.notifications:
            self.notifications.remove(notification)
        notification.destroy()
        
        # если уведомлений больше нет — прячем контейнер nотификаций
        if not self.notifications:
            self.notifications_frame.lower()

        # Reposition remaining notifications
        y_pos = 0
        for n in self.notifications:
            n.place(x=0, y=y_pos, relwidth=1.0)
            y_pos += n.winfo_height() + 10
    
    def on_close(self):
        """Handle application close."""
        try:
            logger.info("Application closing...")
            
            # Показываем индикатор закрытия
            try:
                close_frame = ctk.CTkFrame(self, fg_color=SPOTIFY_COLORS["background"])
                close_frame.place(relx=0.5, rely=0.5, anchor="center", relwidth=1.0, relheight=1.0)
                
                close_label = ctk.CTkLabel(
                    close_frame, 
                    text="Закрытие приложения...", 
                    font=("Helvetica", 16, "bold"),
                    text_color=SPOTIFY_COLORS["text_bright"]
                )
                close_label.place(relx=0.5, rely=0.5, anchor="center")
                
                # Обновляем интерфейс, чтобы показать сообщение
                self.update_idletasks()
            except:
                pass
            
            # Останавливаем мониторинг
            if hasattr(self, 'container_monitor'):
                self.container_monitor.stop_monitoring()
            
            # Сохраняем конфигурацию
            if hasattr(self, 'config'):
                self.config.save()
            
            # Закрываем сессию базы данных, если она существует
            if hasattr(self, 'db_session'):
                self.db_session.close()
            
            # Уничтожаем окно и завершаем процесс
            logger.info("Application closed successfully")
            self.quit()
            import sys
            sys.exit(0)
            
        except Exception as e:
            logger.error(f"Error during application shutdown: {e}")
            import traceback
            logger.error(traceback.format_exc())
            # В случае ошибки принудительно завершаем процесс
            self.quit()
            import sys
            sys.exit(1)

    def open_settings(self):
        """Открывает модальное окно настроек."""
        dlg = SettingsDialog(self, apply_callback=self.apply_settings)
        dlg.grab_set()

    def apply_settings(self, cfg: dict):
        """Применяет новые настройки из SettingsDialog."""
        try:
            # Логируем текущие значения перед изменением
            logger.info(f"Current settings before change: poll_interval={self.container_monitor.refresh_interval}, enable_alerts={self.enable_alerts}")
            
            # polling - устанавливаем новый интервал
            if 'poll_interval' in cfg:
                poll_interval = max(1, cfg['poll_interval'])  # Минимум 1 секунда
                logger.info(f"Setting poll interval to {poll_interval} seconds")
                
                # Устанавливаем новый интервал
                self.container_monitor.set_interval(poll_interval)
                
                # Обновляем конфигурацию
                self.config.set("refresh_interval", poll_interval)
            
            # docker socket
            if 'docker_socket' in cfg and cfg['docker_socket']:
                logger.info(f"Setting Docker socket path to {cfg['docker_socket']}")
                self.docker_client.socket_path = cfg['docker_socket']
            
            # включение/отключение всплывающих алертов
            if 'enable_alerts' in cfg:
                logger.info(f"Setting enable_alerts to {cfg['enable_alerts']}")
                self.enable_alerts = cfg['enable_alerts']
                self.config.set("show_notifications", cfg['enable_alerts'])
            
            # Сохраняем настройки в базе данных, если это не демо-режим
            if not self.demo_mode and self.user_id > 0:
                try:
                    self.settings_service.update_settings(self.user_id, **cfg)
                    logger.info(f"Settings saved to database for user {self.user_id}")
                except Exception as e:
                    logger.error(f"Failed to save settings to database: {e}")
            
            # Сохраняем настройки в конфигурации
            self.config.save()
            
            # Логируем новые значения
            logger.info(f"Settings applied successfully: poll_interval={self.container_monitor.refresh_interval}, enable_alerts={self.enable_alerts}")
            
        except Exception as e:
            logger.error(f"Error applying settings: {e}")
            import traceback
            logger.error(traceback.format_exc())

    def logout(self):
        """Выход из учетной записи пользователя."""
        if messagebox.askyesno("Выход", "Вы уверены, что хотите выйти из учетной записи?"):
            logger.info(f"User {self.user.username if self.user else 'demo'} logging out...")
            
            # Показываем индикатор выхода
            try:
                logout_frame = ctk.CTkFrame(self, fg_color=SPOTIFY_COLORS["background"])
                logout_frame.place(relx=0.5, rely=0.5, anchor="center", relwidth=1.0, relheight=1.0)
                
                logout_label = ctk.CTkLabel(
                    logout_frame, 
                    text="Выполняется выход...", 
                    font=("Helvetica", 16, "bold"),
                    text_color=SPOTIFY_COLORS["text_bright"]
                )
                logout_label.place(relx=0.5, rely=0.5, anchor="center")
                
                # Обновляем интерфейс, чтобы показать сообщение
                self.update_idletasks()
            except:
                pass
            
            # Останавливаем мониторинг
            if hasattr(self, 'container_monitor'):
                self.container_monitor.stop_monitoring()
            
            # Сохраняем конфигурацию
            if hasattr(self, 'config'):
                self.config.save()
            
            # Закрываем сессию базы данных, если она существует
            if hasattr(self, 'db_session'):
                self.db_session.close()
            
            # Создаем новый процесс для запуска приложения
            import subprocess
            import sys
            
            # Запускаем новый экземпляр приложения в отдельном процессе
            subprocess.Popen([sys.executable] + sys.argv)
            
            # Уничтожаем текущее окно и завершаем процесс
            self.quit()
            sys.exit(0)

