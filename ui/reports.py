"""
Reports generation frame for Dockify.
"""
import logging
import time
import tkinter as tk
from tkinter import filedialog, messagebox
from typing import Dict, List, Any, Optional, Callable
import threading
import datetime
import os
import calendar

import customtkinter as ctk

from core.docker_client import DockerClient
from core.monitor import ContainerMonitor
from ui.components import GradientFrame, ActionButton, DropdownSelector, DateSelector
from utils.theme import SPOTIFY_COLORS, lighten_color, scale_color
from utils.exporters import MetricsExporter

# Импорт для работы с базой данных
from db.database import get_db_session
from db.services.report_service import ReportService

logger = logging.getLogger('dockify.ui.reports')

class ReportsFrame(ctk.CTkFrame):
    """
    Reports generation screen for exporting container metrics.
    """
    def __init__(self, parent, docker_client: Any, container_monitor: ContainerMonitor):
        """
        Initialize the reports generation screen.
        
        Args:
            parent: Parent widget
            docker_client: Docker client instance
            container_monitor: Container monitor instance
        """
        super().__init__(parent, corner_radius=0, fg_color=SPOTIFY_COLORS["background"])
        self.parent = parent
        self.docker_client = docker_client
        self.container_monitor = container_monitor
        
        # Exporter
        self.exporter = MetricsExporter(self.container_monitor)
        
        # Currently selected containers
        self.selected_containers: List[str] = []
        
        # Получаем ID пользователя из родительского окна
        self.user_id = getattr(parent, 'user_id', 0)
        
        # Инициализируем сервис отчетов, если это не демо-режим
        self.report_service = None
        if self.user_id > 0:
            try:
                self.db_session = get_db_session()
                self.report_service = ReportService(self.db_session)
            except Exception as e:
                logger.error(f"Failed to initialize report service: {e}")
        
        # Create UI
        self.create_ui()
        
        # Initial data load
        self.refresh()
        
    def create_ui(self):
        """Create and setup the user interface."""
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)  # Header
        self.grid_rowconfigure(1, weight=1)  # Content
        
        # Header with gradient background
        self.header_frame = GradientFrame(
            self, 
            start_color=SPOTIFY_COLORS["accent"],
            end_color=SPOTIFY_COLORS["background"],
            height=120
        )
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=0, pady=(0, 20))
        
        # Header content
        self.header_label = ctk.CTkLabel(
            self.header_frame,
            text="Reports",
            font=("Helvetica", 28, "bold"),
            text_color=SPOTIFY_COLORS["text_bright"]
        )
        self.header_label.place(relx=0.02, rely=0.5, anchor="w")
        
        # Last refresh time
        self.refresh_label = ctk.CTkLabel(
            self.header_frame,
            text="Last updated: Never",
            font=("Helvetica", 12),
            text_color=SPOTIFY_COLORS["text_subtle"]
        )
        self.refresh_label.place(relx=0.98, rely=0.9, anchor="se")
        
        # Main content area
        self.content_frame = ctk.CTkFrame(
            self,
            fg_color=SPOTIFY_COLORS["card_background"],
            corner_radius=10
        )
        self.content_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=0)
        
        # Report configuration
        self.report_config_frame = ctk.CTkFrame(
            self.content_frame,
            fg_color="transparent"
        )
        self.report_config_frame.pack(fill="x", padx=20, pady=20)
        
        # Configure grid for report config
        self.report_config_frame.grid_columnconfigure(0, weight=0)  # Labels
        self.report_config_frame.grid_columnconfigure(1, weight=1)  # Controls
        
        # Section title
        self.config_title = ctk.CTkLabel(
            self.report_config_frame,
            text="Report Configuration",
            font=("Helvetica", 18, "bold"),
            text_color=SPOTIFY_COLORS["text_bright"]
        )
        self.config_title.grid(row=0, column=0, columnspan=2, sticky="w", padx=0, pady=(0, 20))
        
        # Container selection
        self.container_label = ctk.CTkLabel(
            self.report_config_frame,
            text="Containers:",
            font=("Helvetica", 14),
            text_color=SPOTIFY_COLORS["text_bright"],
            width=120,
            anchor="w"
        )
        self.container_label.grid(row=1, column=0, sticky="w", padx=0, pady=(0, 10))
        
        # Container selection frame
        self.container_selection_frame = ctk.CTkFrame(
            self.report_config_frame,
            fg_color=scale_color(SPOTIFY_COLORS["card_background"], 1.1),
            corner_radius=5
        )
        self.container_selection_frame.grid(row=1, column=1, sticky="ew", padx=0, pady=(0, 10))
        
        # Container list scrollable frame
        self.container_list = ctk.CTkScrollableFrame(
            self.container_selection_frame,
            fg_color="transparent",
            height=150
        )
        self.container_list.pack(fill="x", expand=True, padx=10, pady=10)
        
        # Select all button
        self.select_all_var = tk.BooleanVar(value=False)
        self.select_all_checkbox = ctk.CTkCheckBox(
            self.container_list,
            text="Select All",
            font=("Helvetica", 12),
            text_color=SPOTIFY_COLORS["text_bright"],
            fg_color=SPOTIFY_COLORS["accent"],
            hover_color=lighten_color(SPOTIFY_COLORS["accent"], 0.1),
            variable=self.select_all_var,
            command=self.toggle_select_all,
            checkbox_width=20,
            checkbox_height=20
        )
        self.select_all_checkbox.pack(anchor="w", padx=5, pady=(0, 10))
        
        # Container checkboxes will be added dynamically
        self.container_checkboxes = {}
        
        # Time range selection
        self.time_range_label = ctk.CTkLabel(
            self.report_config_frame,
            text="Time range:",
            font=("Helvetica", 14),
            text_color=SPOTIFY_COLORS["text_bright"],
            width=120,
            anchor="w"
        )
        self.time_range_label.grid(row=2, column=0, sticky="w", padx=0, pady=(10, 10))
        
        # Time range frame
        self.time_range_frame = ctk.CTkFrame(
            self.report_config_frame,
            fg_color="transparent"
        )
        self.time_range_frame.grid(row=2, column=1, sticky="ew", padx=0, pady=(10, 10))
        
        # Time range options
        self.time_range_var = tk.StringVar(value="Today")
        
        self.time_today_radio = ctk.CTkRadioButton(
            self.time_range_frame,
            text="Today",
            font=("Helvetica", 12),
            text_color=SPOTIFY_COLORS["text_bright"],
            fg_color=SPOTIFY_COLORS["accent"],
            variable=self.time_range_var,
            value="Today",
            command=self.toggle_custom_date_range
        )
        self.time_today_radio.grid(row=0, column=0, sticky="w", padx=(0, 20), pady=0)
        
        self.time_yesterday_radio = ctk.CTkRadioButton(
            self.time_range_frame,
            text="Yesterday",
            font=("Helvetica", 12),
            text_color=SPOTIFY_COLORS["text_bright"],
            fg_color=SPOTIFY_COLORS["accent"],
            variable=self.time_range_var,
            value="Yesterday",
            command=self.toggle_custom_date_range
        )
        self.time_yesterday_radio.grid(row=0, column=1, sticky="w", padx=(0, 20), pady=0)
        
        self.time_week_radio = ctk.CTkRadioButton(
            self.time_range_frame,
            text="Last 7 days",
            font=("Helvetica", 12),
            text_color=SPOTIFY_COLORS["text_bright"],
            fg_color=SPOTIFY_COLORS["accent"],
            variable=self.time_range_var,
            value="Last 7 days",
            command=self.toggle_custom_date_range
        )
        self.time_week_radio.grid(row=0, column=2, sticky="w", padx=(0, 20), pady=0)
        
        self.time_custom_radio = ctk.CTkRadioButton(
            self.time_range_frame,
            text="Custom range",
            font=("Helvetica", 12),
            text_color=SPOTIFY_COLORS["text_bright"],
            fg_color=SPOTIFY_COLORS["accent"],
            variable=self.time_range_var,
            value="Custom range",
            command=self.toggle_custom_date_range
        )
        self.time_custom_radio.grid(row=0, column=3, sticky="w", padx=0, pady=0)
        
        # Custom date range
        self.custom_date_frame = ctk.CTkFrame(
            self.time_range_frame,
            fg_color="transparent"
        )
        self.custom_date_frame.grid(row=1, column=0, columnspan=4, sticky="ew", padx=0, pady=(10, 0))
        
        # Start date
        self.start_date_label = ctk.CTkLabel(
            self.custom_date_frame,
            text="Start date:",
            font=("Helvetica", 12),
            text_color=SPOTIFY_COLORS["text_subtle"],
            width=80,
            anchor="w"
        )
        self.start_date_label.grid(row=0, column=0, sticky="w", padx=(0, 5), pady=0)
        
        # Use current date as default
        current_date = datetime.datetime.now()
        default_date = current_date.strftime("%Y-%m-%d")
        
        self.start_date_selector = DateSelector(
            self.custom_date_frame,
            label="Start date",
            default_date=default_date,
            width=150
        )
        self.start_date_selector.grid(row=0, column=1, sticky="w", padx=(0, 20), pady=0)
        
        # End date
        self.end_date_label = ctk.CTkLabel(
            self.custom_date_frame,
            text="End date:",
            font=("Helvetica", 12),
            text_color=SPOTIFY_COLORS["text_subtle"],
            width=80,
            anchor="w"
        )
        self.end_date_label.grid(row=0, column=2, sticky="w", padx=(0, 5), pady=0)
        
        self.end_date_selector = DateSelector(
            self.custom_date_frame,
            label="End date",
            default_date=default_date,
            width=150
        )
        self.end_date_selector.grid(row=0, column=3, sticky="w", padx=0, pady=0)
        
        # Initially hide custom date range
        self.custom_date_frame.grid_remove()
        
        # Report format
        self.format_label = ctk.CTkLabel(
            self.report_config_frame,
            text="Format:",
            font=("Helvetica", 14),
            text_color=SPOTIFY_COLORS["text_bright"],
            width=120,
            anchor="w"
        )
        self.format_label.grid(row=3, column=0, sticky="w", padx=0, pady=(10, 10))
        
        self.format_frame = ctk.CTkFrame(
            self.report_config_frame,
            fg_color="transparent"
        )
        self.format_frame.grid(row=3, column=1, sticky="ew", padx=0, pady=(10, 10))
        
        self.format_var = tk.StringVar(value="Excel")
        
        self.format_excel_radio = ctk.CTkRadioButton(
            self.format_frame,
            text="Excel (.xlsx)",
            font=("Helvetica", 12),
            text_color=SPOTIFY_COLORS["text_bright"],
            fg_color=SPOTIFY_COLORS["accent"],
            variable=self.format_var,
            value="Excel"
        )
        self.format_excel_radio.grid(row=0, column=0, sticky="w", padx=(0, 20), pady=0)
        
        self.format_csv_radio = ctk.CTkRadioButton(
            self.format_frame,
            text="CSV (.csv)",
            font=("Helvetica", 12),
            text_color=SPOTIFY_COLORS["text_bright"],
            fg_color=SPOTIFY_COLORS["accent"],
            variable=self.format_var,
            value="CSV"
        )
        self.format_csv_radio.grid(row=0, column=1, sticky="w", padx=(0, 20), pady=0)
        
        # Include graphs option (only for Excel)
        self.include_graphs_var = tk.BooleanVar(value=True)
        self.include_graphs_checkbox = ctk.CTkCheckBox(
            self.format_frame,
            text="Include graphs (Excel only)",
            font=("Helvetica", 12),
            text_color=SPOTIFY_COLORS["text_bright"],
            fg_color=SPOTIFY_COLORS["accent"],
            hover_color=lighten_color(SPOTIFY_COLORS["accent"], 0.1),
            variable=self.include_graphs_var,
            checkbox_width=20,
            checkbox_height=20
        )
        self.include_graphs_checkbox.grid(row=0, column=2, sticky="w", padx=0, pady=0)
        
        # Actions
        self.actions_frame = ctk.CTkFrame(
            self.content_frame,
            fg_color="transparent",
            height=50
        )
        self.actions_frame.pack(fill="x", padx=20, pady=(10, 20))
        
        # Generate report button
        self.generate_button = ctk.CTkButton(
            self.actions_frame,
            text="Generate Report",
            font=("Helvetica", 14, "bold"),
            fg_color=SPOTIFY_COLORS["accent_green"],
            hover_color=lighten_color(SPOTIFY_COLORS["accent_green"], 0.1),
            text_color=SPOTIFY_COLORS["text_bright"],
            width=200,
            height=40,
            command=self.generate_report
        )
        self.generate_button.pack(side="right", padx=0, pady=0)
        
        # Refresh container list button
        self.refresh_button = ctk.CTkButton(
            self.actions_frame,
            text="Refresh Containers",
            font=("Helvetica", 14),
            fg_color=SPOTIFY_COLORS["accent_blue"],
            hover_color=lighten_color(SPOTIFY_COLORS["accent_blue"], 0.1),
            text_color=SPOTIFY_COLORS["text_bright"],
            width=180,
            height=40,
            command=self.refresh
        )
        self.refresh_button.pack(side="left", padx=0, pady=0)
        
        # Report history section
        self.history_frame = ctk.CTkFrame(
            self.content_frame,
            fg_color=scale_color(SPOTIFY_COLORS["card_background"], 1.05),
            corner_radius=5
        )
        self.history_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # History title
        self.history_title = ctk.CTkLabel(
            self.history_frame,
            text="Recent Reports",
            font=("Helvetica", 16, "bold"),
            text_color=SPOTIFY_COLORS["text_bright"]
        )
        self.history_title.pack(anchor="w", padx=15, pady=10)
        
        # History list
        self.history_list = ctk.CTkScrollableFrame(
            self.history_frame,
            fg_color="transparent"
        )
        self.history_list.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # No reports message
        self.no_reports_label = ctk.CTkLabel(
            self.history_list,
            text="No reports generated yet",
            font=("Helvetica", 12),
            text_color=SPOTIFY_COLORS["text_subtle"]
        )
        self.no_reports_label.pack(pady=20)
        
        # Prepare report history items list
        self.report_history_items = []
        
    def refresh(self):
        """Refresh container list and report history."""
        try:
            # Показываем содержимое фрейма сразу
            self.update_idletasks()
            
            # Обновляем метку времени обновления
            self.refresh_label.configure(text=f"Last updated: {time.strftime('%H:%M:%S')}")
            
            # Показываем состояние загрузки
            self.refresh_button.configure(state="disabled", text="Loading...")
            
            # Создаем и показываем индикатор загрузки
            loading_label = ctk.CTkLabel(
                self.content_frame,
                text="Loading data...",
                font=("Helvetica", 14, "bold"),
                text_color=SPOTIFY_COLORS["text_bright"]
            )
            loading_label.place(relx=0.5, rely=0.3, anchor="center")
            
            # Загружаем историю отчетов в фоновом потоке
            threading.Thread(target=self.load_report_history_thread, daemon=True).start()
            
            # Загружаем контейнеры в фоновом потоке
            threading.Thread(
                target=lambda: self.load_containers_with_cleanup(loading_label), 
                daemon=True
            ).start()
            
        except Exception as e:
            logger.error(f"Error refreshing reports view: {e}")
            self.refresh_button.configure(state="normal", text="Refresh Containers")
            
    def load_containers_with_cleanup(self, loading_label):
        """Загружает контейнеры и удаляет индикатор загрузки."""
        try:
            # Загружаем контейнеры
            self.load_containers()
            
            # Удаляем индикатор загрузки
            self.after(0, loading_label.destroy)
        except Exception as e:
            logger.error(f"Error in load_containers_with_cleanup: {e}")
            self.after(0, loading_label.destroy)
            
    def load_report_history_thread(self):
        """Загружает историю отчетов в отдельном потоке."""
        try:
            # Загружаем историю отчетов
            report_files = self.get_report_files()
            
            # Обновляем UI в основном потоке
            self.after(0, lambda: self.update_report_history_ui(report_files))
        except Exception as e:
            logger.error(f"Error loading report history in thread: {e}")
            
    def get_report_files(self):
        """Получает список файлов отчетов из базы данных и файловой системы."""
        report_files = []
        
        # Если есть сервис отчетов и ID пользователя, загружаем отчеты из базы данных
        if self.report_service and self.user_id > 0:
            try:
                # Получаем отчеты пользователя из базы данных
                db_reports = self.report_service.get_reports_by_user(self.user_id, limit=10)
                
                # Добавляем отчеты из базы данных в список
                for report in db_reports:
                    # Проверяем, что файл отчета существует
                    if report.file_path and os.path.exists(report.file_path):
                        report_files.append({
                            "name": os.path.basename(report.file_path),
                            "path": report.file_path,
                            "modified": report.created_at.timestamp(),
                            "db_record": True,
                            "report_id": report.id
                        })
                    else:
                        # Если файл не существует, удаляем запись из базы данных
                        logger.warning(f"Report file not found: {report.file_path}")
                        self.report_service.delete_report(report.id)
            except Exception as e:
                logger.error(f"Error loading reports from database: {e}")
        
        # Также загружаем отчеты из директории (для обратной совместимости)
        reports_dir = os.path.join(os.path.expanduser("~"), "dockify_reports")
        
        # Check if directory exists
        if os.path.exists(reports_dir):
            for file in os.listdir(reports_dir):
                if file.endswith(".xlsx") or file.endswith(".csv"):
                    file_path = os.path.join(reports_dir, file)
                    
                    # Проверяем, что этот файл еще не добавлен из базы данных
                    if not any(r.get("path") == file_path for r in report_files):
                        report_files.append({
                            "name": file,
                            "path": file_path,
                            "modified": os.path.getmtime(file_path),
                            "db_record": False
                        })
        
        # Sort by modification time (newest first)
        report_files.sort(key=lambda x: x["modified"], reverse=True)
        return report_files
        
    def update_report_history_ui(self, report_files):
        """Обновляет UI с историей отчетов."""
        try:
            # Clear existing report history items
            for item in self.report_history_items:
                item.destroy()
            self.report_history_items = []
            
            # Add report items
            for report in report_files[:10]:  # Show last 10 reports
                report_item = ReportHistoryItem(
                    self.history_list,
                    report["name"],
                    datetime.datetime.fromtimestamp(report["modified"]),
                    report["path"]
                )
                report_item.pack(fill="x", padx=5, pady=3)
                self.report_history_items.append(report_item)
                
            # Show/hide no reports message
            if report_files:
                if hasattr(self, 'no_reports_label') and self.no_reports_label.winfo_exists():
                    self.no_reports_label.pack_forget()
            else:
                self.no_reports_label.pack(pady=20)
                
        except Exception as e:
            logger.error(f"Error updating report history UI: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
    def load_containers(self):
        """Load container list in a background thread."""
        try:
            # Get containers
            containers = self.docker_client.list_containers()
            
            # Update UI in main thread
            self.after(0, lambda: self.update_container_list(containers))
            self.after(0, lambda: self.refresh_button.configure(state="normal", text="Refresh Containers"))
        except Exception as e:
            logger.error(f"Error loading containers: {e}")
            self.after(0, lambda: self.refresh_button.configure(state="normal", text="Refresh Containers"))
            
    def update_container_list(self, containers):
        """
        Update the container list with checkboxes.
        
        Args:
            containers: List of container dictionaries
        """
        try:
            # Очищаем существующие чекбоксы контейнеров
            for checkbox_info in self.container_checkboxes.values():
                if isinstance(checkbox_info, dict) and "widget" in checkbox_info and hasattr(checkbox_info["widget"], 'destroy'):
                    checkbox_info["widget"].destroy()
                elif hasattr(checkbox_info, 'destroy'):
                    checkbox_info.destroy()
            self.container_checkboxes = {}
            
            # Создаем словарь контейнеров
            container_map = {}
            container_states = {}
            
            # Обновляем интерфейс, чтобы показать прогресс
            self.update_idletasks()
            
            for container in containers:
                container_id = container.get('Id', '')
                container_name = container.get('Names', [''])[0].lstrip('/')
                container_state = container.get('State', '').lower()
                
                if container_name:
                    display_name = f"{container_name} ({container_id[:12]})"
                    container_map[container_id] = display_name
                    container_states[container_id] = container_state
                    
            # Сортируем контейнеры по имени
            sorted_container_ids = sorted(container_map.keys(), key=lambda cid: container_map[cid])
            
            # Создаем все чекбоксы сразу, но не добавляем их в интерфейс
            checkboxes = []
            for container_id in sorted_container_ids:
                display_name = container_map[container_id]
                is_running = container_states[container_id] == 'running'
                
                # Создаем переменную
                var = tk.BooleanVar(value=False)
                
                # Создаем чекбокс
                checkbox = ctk.CTkCheckBox(
                    self.container_list,
                    text=display_name,
                    font=("Helvetica", 12),
                    text_color=SPOTIFY_COLORS["text_bright"] if is_running else SPOTIFY_COLORS["text_subtle"],
                    fg_color=SPOTIFY_COLORS["accent"],
                    hover_color=lighten_color(SPOTIFY_COLORS["accent"], 0.1),
                    variable=var,
                    command=lambda cid=container_id: self.toggle_container(cid),
                    checkbox_width=20,
                    checkbox_height=20
                )
                
                # Сохраняем чекбокс
                self.container_checkboxes[container_id] = {
                    "widget": checkbox,
                    "variable": var,
                    "display_name": display_name,
                    "is_running": is_running
                }
                
                # Добавляем в список для пакетного добавления
                checkboxes.append((checkbox, container_id))
            
            # Обновляем интерфейс, чтобы показать прогресс
            self.update_idletasks()
            
            # Добавляем все чекбоксы в интерфейс одним пакетом
            for checkbox, _ in checkboxes:
                checkbox.pack(anchor="w", padx=5, pady=2)
                
            # Сбрасываем выбранные контейнеры
            self.selected_containers = []
            
            # Сбрасываем "выбрать все"
            self.select_all_var.set(False)
            
            # Показываем сообщение, если нет контейнеров
            if not containers:
                self.no_containers_label = ctk.CTkLabel(
                    self.container_list,
                    text="No containers available",
                    font=("Helvetica", 12),
                    text_color=SPOTIFY_COLORS["text_subtle"]
                )
                self.no_containers_label.pack(pady=20)
            
            # Восстанавливаем кнопку обновления
            self.refresh_button.configure(state="normal", text="Refresh Containers")
                
        except Exception as e:
            logger.error(f"Error updating container list: {e}")
            self.refresh_button.configure(state="normal", text="Refresh Containers")
            
    def toggle_container(self, container_id):
        """
        Handle container checkbox toggle.
        
        Args:
            container_id: Container ID
        """
        try:
            # Get checkbox state
            is_selected = self.container_checkboxes[container_id]["variable"].get()
            
            # Update selected containers list
            if is_selected and container_id not in self.selected_containers:
                self.selected_containers.append(container_id)
            elif not is_selected and container_id in self.selected_containers:
                self.selected_containers.remove(container_id)
                
            # Update select all checkbox
            if all(info["variable"].get() for info in self.container_checkboxes.values()):
                self.select_all_var.set(True)
            else:
                self.select_all_var.set(False)
                
        except Exception as e:
            logger.error(f"Error toggling container selection: {e}")
            
    def toggle_select_all(self):
        """Handle select all checkbox toggle."""
        try:
            # Get select all state
            select_all = self.select_all_var.get()
            
            # Log the operation
            logger.debug(f"Toggle select all: {select_all}")
            
            # Update selected containers list immediately to maintain consistency
            if select_all:
                self.selected_containers = list(self.container_checkboxes.keys())
            else:
                self.selected_containers = []
            
            # Update all container checkboxes - do this last to ensure UI reflects the state
            for container_id, info in self.container_checkboxes.items():
                if isinstance(info, dict):
                    # Set the variable value first
                    if "variable" in info:
                        info["variable"].set(select_all)
                    
                    # Then update the checkbox widget directly
                    if "widget" in info:
                        if select_all:
                            info["widget"].select()
                        else:
                            info["widget"].deselect()
                            
            # Log the selected containers after the operation
            logger.debug(f"Selected containers after toggle: {len(self.selected_containers)}")
                
        except Exception as e:
            logger.error(f"Error toggling select all: {e}")
            
    def toggle_custom_date_range(self):
        """Show/hide custom date range based on radio button selection."""
        try:
            logger.info(f"Toggle custom date range: {self.time_range_var.get()}")
            if self.time_range_var.get() == "Custom range":
                # Show custom date range
                self.custom_date_frame.grid()
                
                # Make sure date selectors are properly initialized with current date
                current_date = datetime.datetime.now().strftime("%Y-%m-%d")
                
                # Установим даты с разницей в 7 дней для удобства
                start_date = (datetime.datetime.now() - datetime.timedelta(days=7)).strftime("%Y-%m-%d")
                end_date = current_date
                
                # Устанавливаем даты
                self.start_date_selector.set(start_date)
                self.end_date_selector.set(end_date)
                
                # Update UI to ensure proper layout
                self.custom_date_frame.update_idletasks()
                logger.info(f"Custom date range shown with start={start_date}, end={end_date}")
            else:
                # Hide custom date range
                self.custom_date_frame.grid_remove()
                logger.info("Custom date range hidden")
        except Exception as e:
            logger.error(f"Error toggling custom date range: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
    def get_date_range(self) -> tuple:
        """
        Get start and end dates based on selected time range.
        
        Returns:
            Tuple of (start_date, end_date) as datetime objects
        """
        time_range = self.time_range_var.get()
        now = datetime.datetime.now()
        
        if time_range == "Today":
            # Today, midnight to now
            start_date = datetime.datetime(now.year, now.month, now.day, 0, 0, 0)
            end_date = now
        elif time_range == "Yesterday":
            # Yesterday, midnight to midnight
            yesterday = now - datetime.timedelta(days=1)
            start_date = datetime.datetime(yesterday.year, yesterday.month, yesterday.day, 0, 0, 0)
            end_date = datetime.datetime(yesterday.year, yesterday.month, yesterday.day, 23, 59, 59)
        elif time_range == "Last 7 days":
            # Last 7 days
            start_date = now - datetime.timedelta(days=7)
            end_date = now
        elif time_range == "Custom range":
            # Custom range
            start_year, start_month, start_day = self.start_date_selector.get_date()
            end_year, end_month, end_day = self.end_date_selector.get_date()
            
            try:
                start_date = datetime.datetime(start_year, start_month, start_day, 0, 0, 0)
                end_date = datetime.datetime(end_year, end_month, end_day, 23, 59, 59)
            except ValueError as e:
                logger.error(f"Invalid date: {e}")
                messagebox.showerror("Invalid Date", f"Please select a valid date range: {e}")
                raise
        else:
            # Default to today
            start_date = datetime.datetime(now.year, now.month, now.day, 0, 0, 0)
            end_date = now
            
        return start_date, end_date
        
    def generate_report(self):
        """Generate report with selected containers and time range."""
        try:
            # Check if containers are selected
            if not self.selected_containers:
                messagebox.showerror("No Containers Selected", "Please select at least one container for the report.")
                return
                
            # Get date range
            try:
                start_date, end_date = self.get_date_range()
            except Exception:
                return
                
            # Validate date range
            if end_date < start_date:
                messagebox.showerror("Invalid Date Range", "End date must be after start date.")
                return
                
            # Get report format
            report_format = self.format_var.get()
            include_graphs = self.include_graphs_var.get()
            
            # Ask for destination directory
            initial_dir = os.path.join(os.path.expanduser("~"), "dockify_reports")
            if not os.path.exists(initial_dir):
                os.makedirs(initial_dir)
                
            # Create default filename
            date_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            default_filename = f"container_metrics_{date_str}"
            
            if report_format == "Excel":
                file_extension = ".xlsx"
            else:
                file_extension = ".csv"
                
            dest_filepath = filedialog.asksaveasfilename(
                initialdir=initial_dir,
                initialfile=default_filename + file_extension,
                title="Save Report As",
                filetypes=(
                    ("Excel files", "*.xlsx") if report_format == "Excel" else ("CSV files", "*.csv"),
                    ("All files", "*.*")
                )
            )
            
            if not dest_filepath:
                # User cancelled
                return
                
            # Add extension if missing
            if not dest_filepath.endswith(file_extension):
                dest_filepath += file_extension
                
            # Show progress dialog
            progress_dialog = self.create_progress_dialog("Generating Report")
            
            # Generate report in background thread
            threading.Thread(
                target=self.generate_report_thread,
                args=(dest_filepath, report_format, include_graphs, start_date, end_date, progress_dialog),
                daemon=True
            ).start()
            
        except Exception as e:
            logger.error(f"Error preparing report generation: {e}")
            messagebox.showerror("Error", f"Error preparing report: {e}")
            
    def generate_report_thread(self, dest_filepath, report_format, include_graphs, start_date, end_date, progress_dialog):
        """
        Generate report in a background thread.
        
        Args:
            dest_filepath: Destination file path
            report_format: Report format ("Excel" or "CSV")
            include_graphs: Whether to include graphs
            start_date: Start date
            end_date: End date
            progress_dialog: Progress dialog window
        """
        try:
            # Update progress
            self.after(0, lambda: progress_dialog.update_progress(10, "Collecting container data..."))
            
            # Get container display names
            container_names = {}
            for container_id in self.selected_containers:
                if container_id in self.container_checkboxes:
                    container_names[container_id] = self.container_checkboxes[container_id]["display_name"]
                    
            # Update progress
            self.after(0, lambda: progress_dialog.update_progress(30, "Processing metrics..."))
            
            # Generate report
            if report_format == "Excel":
                success = self.exporter.export_to_excel(
                    dest_filepath,
                    self.selected_containers,
                    container_names,
                    start_date,
                    end_date,
                    include_graphs
                )
            else:
                success = self.exporter.export_to_csv(
                    dest_filepath,
                    self.selected_containers,
                    container_names,
                    start_date,
                    end_date
                )
                
            # Update progress
            self.after(0, lambda: progress_dialog.update_progress(90, "Finalizing report..."))
            
            time.sleep(0.5)  # Slight delay for UI
            
            # Close progress dialog
            self.after(0, lambda: progress_dialog.destroy())
            
            if success:
                # Сохраняем отчет в базу данных, если есть сервис отчетов и ID пользователя
                if self.report_service and self.user_id > 0:
                    try:
                        # Создаем запись в базе данных
                        report_title = os.path.basename(dest_filepath)
                        report_type = "excel" if report_format == "Excel" else "csv"
                        
                        # Параметры отчета
                        parameters = {
                            "containers": [
                                {"id": container_id, "name": container_names.get(container_id, container_id)}
                                for container_id in self.selected_containers
                            ],
                            "include_graphs": include_graphs
                        }
                        
                        # Создаем отчет
                        self.report_service.create_report(
                            user_id=self.user_id,
                            title=report_title,
                            report_type=report_type,
                            file_path=dest_filepath,
                            start_date=start_date,
                            end_date=end_date,
                            description=f"Report for {len(self.selected_containers)} containers",
                            parameters=parameters
                        )
                        
                        logger.info(f"Report saved to database: {report_title}")
                    except Exception as e:
                        logger.error(f"Error saving report to database: {e}")
                
                # Show success message
                self.after(0, lambda: messagebox.showinfo("Report Generated", 
                                                        f"Report successfully generated at:\n{dest_filepath}"))
                                                        
                # Refresh report history
                self.after(0, self.load_report_history_thread)
            else:
                self.after(0, lambda: messagebox.showerror("Error", 
                                                         "Failed to generate report. Check logs for details."))
                                                         
        except Exception as e:
            logger.error(f"Error generating report: {e}")
            self.after(0, lambda: progress_dialog.destroy())
            self.after(0, lambda: messagebox.showerror("Error", f"Error generating report: {e}"))
            
    def create_progress_dialog(self, title):
        """
        Create a progress dialog window.
        
        Args:
            title: Dialog title
            
        Returns:
            ProgressDialog instance
        """
        return ProgressDialog(self, title)

    def load_report_history(self):
        """
        Метод для обратной совместимости.
        Теперь использует асинхронную загрузку через load_report_history_thread.
        """
        threading.Thread(target=self.load_report_history_thread, daemon=True).start()


class ReportHistoryItem(ctk.CTkFrame):
    """
    Report history item widget for displaying a generated report.
    """
    def __init__(self, parent, report_name, report_date, report_path):
        """
        Initialize report history item.
        
        Args:
            parent: Parent widget
            report_name: Report file name
            report_date: Report generation date
            report_path: Report file path
        """
        super().__init__(
            parent,
            fg_color=scale_color(SPOTIFY_COLORS["card_background"], 1.1),
            corner_radius=5,
            height=50
        )
        
        self.report_path = report_path
        
        # Create UI
        self.grid_columnconfigure(0, weight=1)
        
        # Report name
        self.name_label = ctk.CTkLabel(
            self,
            text=report_name,
            font=("Helvetica", 12, "bold"),
            text_color=SPOTIFY_COLORS["text_bright"],
            anchor="w"
        )
        self.name_label.grid(row=0, column=0, sticky="w", padx=10, pady=(10, 5))
        
        # Report date
        self.date_label = ctk.CTkLabel(
            self,
            text=f"Generated: {report_date.strftime('%Y-%m-%d %H:%M:%S')}",
            font=("Helvetica", 10),
            text_color=SPOTIFY_COLORS["text_subtle"],
            anchor="w"
        )
        self.date_label.grid(row=1, column=0, sticky="w", padx=10, pady=(0, 10))
        
        # Open button
        self.open_button = ctk.CTkButton(
            self,
            text="Open",
            font=("Helvetica", 11),
            fg_color=SPOTIFY_COLORS["accent_blue"],
            hover_color=lighten_color(SPOTIFY_COLORS["accent_blue"], 0.1),
            text_color=SPOTIFY_COLORS["text_bright"],
            width=60,
            height=25,
            command=self.open_report
        )
        self.open_button.grid(row=0, column=1, rowspan=2, padx=10, pady=0)
        
    def open_report(self):
        """Open the report file."""
        try:
            # Use platform-specific command to open the file
            import platform
            import subprocess
            
            if platform.system() == 'Windows':
                os.startfile(self.report_path)
            elif platform.system() == 'Darwin':  # macOS
                subprocess.call(('open', self.report_path))
            else:  # Linux
                subprocess.call(('xdg-open', self.report_path))
                
        except Exception as e:
            logger.error(f"Error opening report: {e}")
            messagebox.showerror("Error", f"Error opening report: {e}")


class ProgressDialog(ctk.CTkToplevel):
    """
    Progress dialog for long-running operations.
    """
    def __init__(self, parent, title, width=400, height=150):
        """
        Initialize progress dialog.
        
        Args:
            parent: Parent widget
            title: Dialog title
            width: Dialog width
            height: Dialog height
        """
        super().__init__(parent)
        self.title(title)
        self.geometry(f"{width}x{height}")
        self.resizable(False, False)
        
        # Make modal
        self.transient(parent)
        self.grab_set()
        
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Content frame
        self.content_frame = ctk.CTkFrame(
            self,
            fg_color=SPOTIFY_COLORS["card_background"],
            corner_radius=0
        )
        self.content_frame.grid(row=0, column=0, sticky="nsew")
        
        # Status message
        self.status_label = ctk.CTkLabel(
            self.content_frame,
            text="Initializing...",
            font=("Helvetica", 14),
            text_color=SPOTIFY_COLORS["text_bright"]
        )
        self.status_label.pack(pady=(30, 15))
        
        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(
            self.content_frame,
            width=300,
            height=15,
            corner_radius=2,
            fg_color=scale_color(SPOTIFY_COLORS["card_background"], 1.2),
            progress_color=SPOTIFY_COLORS["accent_green"]
        )
        self.progress_bar.pack(pady=(0, 20))
        self.progress_bar.set(0)
        
        # Center on parent
        self.update_idletasks()
        parent_x = parent.winfo_rootx()
        parent_y = parent.winfo_rooty()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()
        
        x = parent_x + (parent_width - width) // 2
        y = parent_y + (parent_height - height) // 2
        
        self.geometry(f"+{x}+{y}")
        
    def update_progress(self, value, status=None):
        """
        Update progress and status message.
        
        Args:
            value: Progress value (0-100)
            status: Status message (optional)
        """
        self.progress_bar.set(value / 100.0)
        
        if status:
            self.status_label.configure(text=status)
