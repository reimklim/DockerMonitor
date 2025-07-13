"""
Containers view for Dockify.
"""
import logging
import time
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, List, Any, Optional, Callable, Tuple, Union

import customtkinter as ctk

from core.docker_client import DockerClient
from ui.components import GradientFrame, ActionButton, StatusIndicator, CardFrame
from utils.theme import SPOTIFY_COLORS, lighten_color, scale_color
from utils.compat import get_compatible_color

logger = logging.getLogger('dockify.ui.containers')

class ContainersFrame(ctk.CTkFrame):
    """
    Containers management screen for viewing and controlling Docker containers.
    """
    def __init__(self, parent, docker_client: Any):
        """
        Initialize the containers management screen.
        
        Args:
            parent: Parent widget
            docker_client: Docker client instance
        """
        super().__init__(parent, corner_radius=0, fg_color=SPOTIFY_COLORS["background"])
        self.parent = parent
        self.docker_client = docker_client
        
        # Container for current metrics
        self.current_metrics: Dict[str, Dict[str, Any]] = {}
        
        # Selected container ID and name
        self.selected_container: Optional[str] = None
        self.selected_container_name: Optional[str] = None
        
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
            text="Containers",
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
        
        # Refresh button
        self.refresh_button = ctk.CTkButton(
            self.header_frame,
            text="Refresh",
            font=("Helvetica", 12),
            fg_color=SPOTIFY_COLORS["accent_green"],
            hover_color=lighten_color(SPOTIFY_COLORS["accent_green"], 0.1),
            text_color=SPOTIFY_COLORS["text_bright"],
            width=100,
            command=self.refresh
        )
        self.refresh_button.place(relx=0.85, rely=0.5, anchor="e")
        
        # Content area
        self.content_frame = ctk.CTkFrame(self, fg_color=get_compatible_color("transparent"))
        self.content_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=0)
        self.content_frame.grid_columnconfigure(0, weight=2)
        self.content_frame.grid_columnconfigure(1, weight=3)
        self.content_frame.grid_rowconfigure(0, weight=1)
        
        # Container list frame
        self.list_frame = ctk.CTkFrame(
            self.content_frame,
            fg_color=SPOTIFY_COLORS["card_background"],
            corner_radius=10
        )
        self.list_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=0)
        
        # List header
        self.list_header = ctk.CTkFrame(
            self.list_frame,
            fg_color="transparent",
            height=40
        )
        self.list_header.pack(fill="x", padx=10, pady=(10, 0))
        
        # Search box
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self.filter_containers)
        
        self.search_entry = ctk.CTkEntry(
            self.list_header,
            placeholder_text="Search containers...",
            font=("Helvetica", 12),
            text_color=SPOTIFY_COLORS["text_bright"],
            fg_color=scale_color(SPOTIFY_COLORS["card_background"], 1.15),
            border_color=SPOTIFY_COLORS["border"],
            width=200,
            textvariable=self.search_var
        )
        self.search_entry.pack(side="left", fill="x", expand=True, pady=5)
        
        # Filter dropdown
        self.filter_var = tk.StringVar(value="All")
        self.filter_dropdown = ctk.CTkOptionMenu(
            self.list_header,
            values=["All", "Running", "Stopped"],
            font=("Helvetica", 12),
            text_color=SPOTIFY_COLORS["text_bright"],
            fg_color=SPOTIFY_COLORS["accent"],
            button_color=SPOTIFY_COLORS["accent"],
            button_hover_color=lighten_color(SPOTIFY_COLORS["accent"], 0.1),
            dropdown_fg_color=scale_color(SPOTIFY_COLORS["card_background"], 1.1),
            variable=self.filter_var,
            command=self.filter_containers
        )
        self.filter_dropdown.pack(side="right", padx=(10, 0), pady=5)
        
        # Container list
        self.container_list = ctk.CTkScrollableFrame(
            self.list_frame,
            fg_color="transparent"
        )
        self.container_list.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Container details frame
        self.details_frame = ctk.CTkFrame(
            self.content_frame,
            fg_color=SPOTIFY_COLORS["card_background"],
            corner_radius=10
        )
        self.details_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 0), pady=0)
        
        # Details header
        self.details_header = ctk.CTkFrame(
            self.details_frame,
            fg_color="transparent",
            height=50
        )
        self.details_header.pack(fill="x", padx=15, pady=10)
        
        # Container name label
        self.container_name_label = ctk.CTkLabel(
            self.details_header,
            text="No container selected",
            font=("Helvetica", 18, "bold"),
            text_color=SPOTIFY_COLORS["text_bright"]
        )
        self.container_name_label.pack(side="left", anchor="w")
        
        # Actions frame for buttons
        self.actions_frame = ctk.CTkFrame(
            self.details_header,
            fg_color="transparent"
        )
        self.actions_frame.pack(side="right", anchor="e")
        
        # Action buttons
        try:
            self.start_button = ActionButton(
                self.actions_frame,
                text="Start",
                icon_name="play",
                button_type="primary",
                fg_color=SPOTIFY_COLORS["accent_green"],
                text_color="#FFFFFF",  # Белый текст для лучшей видимости
                font=("Helvetica", 12, "bold"),  # Жирный шрифт
                command=self.start_container
            )
        except Exception as e:
            logger.warning(f"Failed to create start button with icon: {e}")
            self.start_button = ctk.CTkButton(
                self.actions_frame,
                text="Start",
                fg_color=SPOTIFY_COLORS["accent_green"],
                text_color="#FFFFFF",
                font=("Helvetica", 12, "bold"),
                command=self.start_container
            )
        self.start_button.pack(side="left", padx=5)
        
        try:
            self.stop_button = ActionButton(
                self.actions_frame,
                text="Stop",
                icon_name="stop",
                button_type="primary",
                fg_color=SPOTIFY_COLORS["accent_orange"],
                text_color="#FFFFFF",  # Белый текст для лучшей видимости
                font=("Helvetica", 12, "bold"),  # Жирный шрифт
                command=self.stop_container
            )
        except Exception as e:
            logger.warning(f"Failed to create stop button with icon: {e}")
            self.stop_button = ctk.CTkButton(
                self.actions_frame,
                text="Stop",
                fg_color=SPOTIFY_COLORS["accent_orange"],
                text_color="#FFFFFF",
                font=("Helvetica", 12, "bold"),
                command=self.stop_container
            )
        self.stop_button.pack(side="left", padx=5)
        
        try:
            self.restart_button = ActionButton(
                self.actions_frame,
                text="Restart",
                icon_name="refresh",
                button_type="primary",
                fg_color=SPOTIFY_COLORS["accent_blue"],
                text_color="#FFFFFF",  # Белый текст для лучшей видимости
                font=("Helvetica", 12, "bold"),  # Жирный шрифт
                command=self.restart_container
            )
        except Exception as e:
            logger.warning(f"Failed to create restart button with icon: {e}")
            self.restart_button = ctk.CTkButton(
                self.actions_frame,
                text="Restart",
                fg_color=SPOTIFY_COLORS["accent_blue"],
                text_color="#FFFFFF",
                font=("Helvetica", 12, "bold"),
                command=self.restart_container
            )
        self.restart_button.pack(side="left", padx=5)
        
        try:
            self.delete_button = ActionButton(
                self.actions_frame,
                text="Delete",
                icon_name="trash",
                button_type="primary",
                fg_color=SPOTIFY_COLORS["accent_red"],
                text_color="#FFFFFF",  # Белый текст для лучшей видимости
                font=("Helvetica", 12, "bold"),  # Жирный шрифт
                command=self.delete_container
            )
        except Exception as e:
            logger.warning(f"Failed to create delete button with icon: {e}")
            self.delete_button = ctk.CTkButton(
                self.actions_frame,
                text="Delete",
                fg_color=SPOTIFY_COLORS["accent_red"],
                text_color="#FFFFFF",
                font=("Helvetica", 12, "bold"),
                command=self.delete_container
            )
        self.delete_button.pack(side="left", padx=5)
        
        # Details content - using tabs for organization
        self.details_tabs = ctk.CTkTabview(
            self.details_frame,
            fg_color=get_compatible_color("transparent"),
            segmented_button_fg_color=scale_color(SPOTIFY_COLORS["card_background"], 1.1),
            segmented_button_selected_color=SPOTIFY_COLORS["accent"],
            segmented_button_selected_hover_color=lighten_color(SPOTIFY_COLORS["accent"], 0.1),
            segmented_button_unselected_color=scale_color(SPOTIFY_COLORS["card_background"], 1.15),
            segmented_button_unselected_hover_color=scale_color(SPOTIFY_COLORS["card_background"], 1.2),
            text_color=SPOTIFY_COLORS["text_bright"]
        )
        self.details_tabs.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        # Create tabs
        self.overview_tab = self.details_tabs.add("Overview")
        self.logs_tab = self.details_tabs.add("Logs")
        self.inspect_tab = self.details_tabs.add("Inspect")
        
        # Overview tab content
        self.overview_tab.grid_columnconfigure((0, 1), weight=1)
        
        # Status section
        self.status_frame = ctk.CTkFrame(
            self.overview_tab,
            fg_color=scale_color(SPOTIFY_COLORS["card_background"], 1.05),
            corner_radius=5
        )
        self.status_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=10)
        
        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="Status:",
            font=("Helvetica", 12),
            text_color=SPOTIFY_COLORS["text_subtle"]
        )
        self.status_label.grid(row=0, column=0, sticky="w", padx=10, pady=10)
        
        self.status_value = ctk.CTkLabel(
            self.status_frame,
            text="N/A",
            font=("Helvetica", 12, "bold"),
            text_color=SPOTIFY_COLORS["text_bright"]
        )
        self.status_value.grid(row=0, column=1, sticky="w", padx=0, pady=10)
        
        self.created_label = ctk.CTkLabel(
            self.status_frame,
            text="Created:",
            font=("Helvetica", 12),
            text_color=SPOTIFY_COLORS["text_subtle"]
        )
        self.created_label.grid(row=1, column=0, sticky="w", padx=10, pady=10)
        
        self.created_value = ctk.CTkLabel(
            self.status_frame,
            text="N/A",
            font=("Helvetica", 12),
            text_color=SPOTIFY_COLORS["text_bright"]
        )
        self.created_value.grid(row=1, column=1, sticky="w", padx=0, pady=10)
        
        # Metrics section
        self.metrics_frame = ctk.CTkFrame(
            self.overview_tab,
            fg_color=scale_color(SPOTIFY_COLORS["card_background"], 1.05),
            corner_radius=5
        )
        self.metrics_frame.grid(row=1, column=0, sticky="nsew", padx=(10, 5), pady=10)
        
        self.metrics_title = ctk.CTkLabel(
            self.metrics_frame,
            text="Resource Usage",
            font=("Helvetica", 14, "bold"),
            text_color=SPOTIFY_COLORS["text_bright"]
        )
        self.metrics_title.pack(anchor="w", padx=10, pady=(10, 5))
        
        # CPU usage
        self.cpu_frame = ctk.CTkFrame(
            self.metrics_frame,
            fg_color="transparent"
        )
        self.cpu_frame.pack(fill="x", padx=10, pady=5)
        
        self.cpu_label = ctk.CTkLabel(
            self.cpu_frame,
            text="CPU Usage:",
            font=("Helvetica", 12),
            text_color=SPOTIFY_COLORS["text_subtle"],
            width=120,
            anchor="w"
        )
        self.cpu_label.pack(side="left")
        
        self.cpu_value = ctk.CTkLabel(
            self.cpu_frame,
            text="0%",
            font=("Helvetica", 12, "bold"),
            text_color=SPOTIFY_COLORS["accent_green"]
        )
        self.cpu_value.pack(side="left")
        
        self.cpu_progress = ctk.CTkProgressBar(
            self.metrics_frame,
            width=200,
            height=10,
            corner_radius=2,
            fg_color=scale_color(SPOTIFY_COLORS["card_background"], 1.2),
            progress_color=SPOTIFY_COLORS["accent_green"]
        )
        self.cpu_progress.pack(fill="x", padx=10, pady=(0, 10))
        self.cpu_progress.set(0)
        
        # Memory usage
        self.memory_frame = ctk.CTkFrame(
            self.metrics_frame,
            fg_color="transparent"
        )
        self.memory_frame.pack(fill="x", padx=10, pady=5)
        
        self.memory_label = ctk.CTkLabel(
            self.memory_frame,
            text="Memory Usage:",
            font=("Helvetica", 12),
            text_color=SPOTIFY_COLORS["text_subtle"],
            width=120,
            anchor="w"
        )
        self.memory_label.pack(side="left")
        
        self.memory_value = ctk.CTkLabel(
            self.memory_frame,
            text="0 MB (0%)",
            font=("Helvetica", 12, "bold"),
            text_color=SPOTIFY_COLORS["accent_purple"]
        )
        self.memory_value.pack(side="left")
        
        self.memory_progress = ctk.CTkProgressBar(
            self.metrics_frame,
            width=200,
            height=10,
            corner_radius=2,
            fg_color=scale_color(SPOTIFY_COLORS["card_background"], 1.2),
            progress_color=SPOTIFY_COLORS["accent_purple"]
        )
        self.memory_progress.pack(fill="x", padx=10, pady=(0, 10))
        self.memory_progress.set(0)
        
        # Network usage
        self.network_frame = ctk.CTkFrame(
            self.metrics_frame,
            fg_color="transparent"
        )
        self.network_frame.pack(fill="x", padx=10, pady=5)
        
        self.network_label = ctk.CTkLabel(
            self.network_frame,
            text="Network I/O:",
            font=("Helvetica", 12),
            text_color=SPOTIFY_COLORS["text_subtle"],
            width=120,
            anchor="w"
        )
        self.network_label.pack(side="left")
        
        self.network_value = ctk.CTkLabel(
            self.network_frame,
            text="0 KB / 0 KB",
            font=("Helvetica", 12, "bold"),
            text_color=SPOTIFY_COLORS["accent_blue"]
        )
        self.network_value.pack(side="left")
        
        # Container info section
        self.info_frame = ctk.CTkFrame(
            self.overview_tab,
            fg_color=scale_color(SPOTIFY_COLORS["card_background"], 1.05),
            corner_radius=5
        )
        self.info_frame.grid(row=1, column=1, sticky="nsew", padx=(5, 10), pady=10)
        
        self.info_title = ctk.CTkLabel(
            self.info_frame,
            text="Container Info",
            font=("Helvetica", 14, "bold"),
            text_color=SPOTIFY_COLORS["text_bright"]
        )
        self.info_title.pack(anchor="w", padx=10, pady=(10, 5))
        
        # Add resource limits section
        self.limits_frame = ctk.CTkFrame(
            self.info_frame,
            fg_color="transparent"
        )
        self.limits_frame.pack(fill="x", padx=10, pady=5)
        
        self.limits_title = ctk.CTkLabel(
            self.limits_frame,
            text="Resource Limits",
            font=("Helvetica", 12, "bold"),
            text_color=SPOTIFY_COLORS["text_bright"]
        )
        self.limits_title.pack(anchor="w", pady=(5, 10))
        
        # CPU Limit
        self.cpu_limit_frame = ctk.CTkFrame(
            self.limits_frame,
            fg_color="transparent"
        )
        self.cpu_limit_frame.pack(fill="x", pady=5)
        
        self.cpu_limit_label = ctk.CTkLabel(
            self.cpu_limit_frame,
            text="CPU Alert Limit:",
            font=("Helvetica", 12),
            text_color=SPOTIFY_COLORS["text_subtle"],
            width=120,
            anchor="w"
        )
        self.cpu_limit_label.pack(side="left")
        
        self.cpu_limit_var = tk.StringVar(value="80")
        self.cpu_limit_entry = ctk.CTkEntry(
            self.cpu_limit_frame,
            width=60,
            textvariable=self.cpu_limit_var
        )
        self.cpu_limit_entry.pack(side="left", padx=(5, 0))
        
        self.cpu_limit_percent = ctk.CTkLabel(
            self.cpu_limit_frame,
            text="%",
            font=("Helvetica", 12),
            text_color=SPOTIFY_COLORS["text_subtle"]
        )
        self.cpu_limit_percent.pack(side="left")
        
        # Memory Limit
        self.memory_limit_frame = ctk.CTkFrame(
            self.limits_frame,
            fg_color="transparent"
        )
        self.memory_limit_frame.pack(fill="x", pady=5)
        
        self.memory_limit_label = ctk.CTkLabel(
            self.memory_limit_frame,
            text="Memory Alert Limit:",
            font=("Helvetica", 12),
            text_color=SPOTIFY_COLORS["text_subtle"],
            width=120,
            anchor="w"
        )
        self.memory_limit_label.pack(side="left")
        
        self.memory_limit_var = tk.StringVar(value="80")
        self.memory_limit_entry = ctk.CTkEntry(
            self.memory_limit_frame,
            width=60,
            textvariable=self.memory_limit_var
        )
        self.memory_limit_entry.pack(side="left", padx=(5, 0))
        
        self.memory_limit_percent = ctk.CTkLabel(
            self.memory_limit_frame,
            text="%",
            font=("Helvetica", 12),
            text_color=SPOTIFY_COLORS["text_subtle"]
        )
        self.memory_limit_percent.pack(side="left")
        
        # Apply Button
        self.apply_limits_button = ctk.CTkButton(
            self.limits_frame,
            text="Apply Limits",
            fg_color=SPOTIFY_COLORS["accent"],
            text_color="#FFFFFF",  # Белый текст для лучшей видимости
            hover_color=lighten_color(SPOTIFY_COLORS["accent"], 0.1),
            font=("Helvetica", 12, "bold"),  # Жирный шрифт
            command=self.apply_resource_limits
        )
        self.apply_limits_button.pack(pady=(10, 5))
        
        # Container ID
        self.id_frame = ctk.CTkFrame(
            self.info_frame,
            fg_color="transparent"
        )
        self.id_frame.pack(fill="x", padx=10, pady=5)
        
        self.id_label = ctk.CTkLabel(
            self.id_frame,
            text="Container ID:",
            font=("Helvetica", 12),
            text_color=SPOTIFY_COLORS["text_subtle"],
            width=120,
            anchor="w"
        )
        self.id_label.pack(side="left")
        
        self.id_value = ctk.CTkLabel(
            self.id_frame,
            text="N/A",
            font=("Helvetica", 12),
            text_color=SPOTIFY_COLORS["text_bright"]
        )
        self.id_value.pack(side="left")
        
        # Image
        self.image_frame = ctk.CTkFrame(
            self.info_frame,
            fg_color="transparent"
        )
        self.image_frame.pack(fill="x", padx=10, pady=5)
        
        self.image_label = ctk.CTkLabel(
            self.image_frame,
            text="Image:",
            font=("Helvetica", 12),
            text_color=SPOTIFY_COLORS["text_subtle"],
            width=120,
            anchor="w"
        )
        self.image_label.pack(side="left")
        
        self.image_value = ctk.CTkLabel(
            self.image_frame,
            text="N/A",
            font=("Helvetica", 12),
            text_color=SPOTIFY_COLORS["text_bright"]
        )
        self.image_value.pack(side="left")
        
        # Command
        self.command_frame = ctk.CTkFrame(
            self.info_frame,
            fg_color="transparent"
        )
        self.command_frame.pack(fill="x", padx=10, pady=5)
        
        self.command_label = ctk.CTkLabel(
            self.command_frame,
            text="Command:",
            font=("Helvetica", 12),
            text_color=SPOTIFY_COLORS["text_subtle"],
            width=120,
            anchor="w"
        )
        self.command_label.pack(side="left")
        
        self.command_value = ctk.CTkLabel(
            self.command_frame,
            text="N/A",
            font=("Helvetica", 12),
            text_color=SPOTIFY_COLORS["text_bright"]
        )
        self.command_value.pack(side="left")
        
        # Ports
        self.ports_frame = ctk.CTkFrame(
            self.info_frame,
            fg_color="transparent"
        )
        self.ports_frame.pack(fill="x", padx=10, pady=5)
        
        self.ports_label = ctk.CTkLabel(
            self.ports_frame,
            text="Ports:",
            font=("Helvetica", 12),
            text_color=SPOTIFY_COLORS["text_subtle"],
            width=120,
            anchor="w"
        )
        self.ports_label.pack(side="left")
        
        self.ports_value = ctk.CTkLabel(
            self.ports_frame,
            text="N/A",
            font=("Helvetica", 12),
            text_color=SPOTIFY_COLORS["text_bright"]
        )
        self.ports_value.pack(side="left")
        
        # Logs tab content
        self.logs_tab.grid_columnconfigure(0, weight=1)
        self.logs_tab.grid_rowconfigure(1, weight=1)
        
        # Logs controls
        self.logs_controls = ctk.CTkFrame(
            self.logs_tab,
            fg_color="transparent"
        )
        self.logs_controls.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        
        self.logs_refresh_button = ctk.CTkButton(
            self.logs_controls,
            text="Refresh Logs",
            font=("Helvetica", 12),
            fg_color=SPOTIFY_COLORS["accent_blue"],
            hover_color=lighten_color(SPOTIFY_COLORS["accent_blue"], 0.1),
            text_color=SPOTIFY_COLORS["text_bright"],
            width=120,
            command=self.refresh_logs
        )
        self.logs_refresh_button.pack(side="left", padx=5)
        
        self.logs_tail_label = ctk.CTkLabel(
            self.logs_controls,
            text="Tail:",
            font=("Helvetica", 12),
            text_color=SPOTIFY_COLORS["text_subtle"]
        )
        self.logs_tail_label.pack(side="left", padx=(10, 5))
        
        self.logs_tail_var = tk.StringVar(value="100")
        self.logs_tail_entry = ctk.CTkEntry(
            self.logs_controls,
            width=60,
            textvariable=self.logs_tail_var,
            font=("Helvetica", 12),
            text_color=SPOTIFY_COLORS["text_bright"],
            fg_color=scale_color(SPOTIFY_COLORS["card_background"], 1.15),
            border_color=SPOTIFY_COLORS["border"]
        )
        self.logs_tail_entry.pack(side="left", padx=5)
        
        # Logs content
        self.logs_frame = ctk.CTkFrame(
            self.logs_tab,
            fg_color=scale_color(SPOTIFY_COLORS["card_background"], 1.05),
            corner_radius=5
        )
        self.logs_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(5, 10))
        
        self.logs_text = ctk.CTkTextbox(
            self.logs_frame,
            font=("Courier New", 11),
            text_color=SPOTIFY_COLORS["text_bright"],
            fg_color="transparent",
            border_width=0,
            wrap="none"
        )
        self.logs_text.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Inspect tab content
        self.inspect_tab.grid_columnconfigure(0, weight=1)
        self.inspect_tab.grid_rowconfigure(0, weight=1)
        
        self.inspect_frame = ctk.CTkFrame(
            self.inspect_tab,
            fg_color=scale_color(SPOTIFY_COLORS["card_background"], 1.05),
            corner_radius=5
        )
        self.inspect_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        self.inspect_text = ctk.CTkTextbox(
            self.inspect_frame,
            font=("Courier New", 11),
            text_color=SPOTIFY_COLORS["text_bright"],
            fg_color="transparent",
            border_width=0,
            wrap="none"
        )
        self.inspect_text.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Initial state of action buttons
        self.update_action_buttons(None)
        
        # Container items list
        self.container_items = {}
        
    def refresh(self):
        """Refresh container list and details."""
        try:
            # Show loading state
            self.refresh_button.configure(state="disabled", text="Loading...")
            
            # Save current container name before refresh
            if self.selected_container:
                current_name = self.container_name_label.cget("text")
                if current_name and current_name != "No container selected":
                    self.selected_container_name = current_name
            
            # Load containers in a background thread
            threading.Thread(target=self.load_containers, daemon=True).start()
            
            # Update refresh time
            self.refresh_label.configure(text=f"Last updated: {time.strftime('%H:%M:%S')}")
        except Exception as e:
            logger.error(f"Error refreshing containers: {e}")
            self.refresh_button.configure(state="normal", text="Refresh")
            
    def load_containers(self):
        """Load container list in a background thread."""
        try:
            # Get containers
            containers = self.docker_client.list_containers()
            
            # Update UI in main thread
            self.after(0, lambda: self.update_container_list(containers))
            self.after(0, lambda: self.refresh_button.configure(state="normal", text="Refresh"))
        except Exception as e:
            logger.error(f"Error loading containers: {e}")
            self.after(0, lambda: self.refresh_button.configure(state="normal", text="Refresh"))
            
    def update_container_list(self, containers):
        """
        Update the container list.
        
        Args:
            containers: List of container dictionaries
        """
        try:
            # Clear existing items first if filter or search changed
            if hasattr(self, 'last_filter') and (
                self.last_filter != self.filter_var.get() or
                hasattr(self, 'last_search') and self.last_search != self.search_var.get()
            ):
                for item in self.container_items.values():
                    item.destroy()
                self.container_items = {}
                
            # Track existing container IDs
            existing_ids = set(self.container_items.keys())
            new_ids = set()
            
            # Apply filter
            filtered_containers = []
            filter_value = self.filter_var.get()
            search_value = self.search_var.get().lower()
            
            for container in containers:
                # Get container name
                container_name = container.get('Names', [''])[0].lstrip('/')
                
                # Apply status filter
                if filter_value == "Running" and container.get('State', '').lower() != 'running':
                    continue
                elif filter_value == "Stopped" and container.get('State', '').lower() == 'running':
                    continue
                    
                # Apply search filter
                if search_value and search_value not in container_name.lower():
                    continue
                    
                filtered_containers.append(container)
                
            # Remember current filter and search for next update
            self.last_filter = filter_value
            self.last_search = search_value
            
            # Add or update containers
            for container in filtered_containers:
                container_id = container.get('Id', '')
                new_ids.add(container_id)
                
                # Get metrics if available
                metrics = self.current_metrics.get(container_id, {})
                
                if container_id in existing_ids:
                    # Update existing container
                    self.container_items[container_id].update(container, metrics)
                else:
                    # Create new container item
                    container_item = ContainerListItem(
                        self.container_list, 
                        container, 
                        metrics,
                        command=lambda cid=container_id: self.select_container(cid)
                    )
                    container_item.pack(fill="x", padx=5, pady=3)
                    self.container_items[container_id] = container_item
                    
            # Remove containers that no longer exist or don't match filter
            for container_id in existing_ids - new_ids:
                self.container_items[container_id].destroy()
                del self.container_items[container_id]
                
            # If selected container was removed, clear selection
            if self.selected_container and self.selected_container not in new_ids:
                self.select_container(None)
                
            # Show message if no containers
            if not filtered_containers:
                if not hasattr(self, 'no_containers_label') or not self.no_containers_label.winfo_exists():
                    self.no_containers_label = ctk.CTkLabel(
                        self.container_list,
                        text="No containers found",
                        font=("Helvetica", 12),
                        text_color=SPOTIFY_COLORS["text_subtle"]
                    )
                    self.no_containers_label.pack(pady=10)
            elif hasattr(self, 'no_containers_label') and self.no_containers_label.winfo_exists():
                self.no_containers_label.destroy()
                
            # Mark selected container in the list
            if self.selected_container:
                for container_id, item in self.container_items.items():
                    item.set_selected(container_id == self.selected_container)
                
        except Exception as e:
            logger.error(f"Error updating container list: {e}")
            
    def filter_containers(self, *args):
        """Filter containers based on search text and filter dropdown."""
        # Re-apply the container list using the current containers
        self.refresh()
            
    def select_container(self, container_id):
        """
        Select a container and show its details.
        
        Args:
            container_id: Container ID or None to clear selection
        """
        # Update selected container
        self.selected_container = container_id
        
        # Store the container name if available (for maintaining during auto-refresh)
        if container_id is not None and container_id in self.container_items:
            # Get the name from the container item
            item = self.container_items[container_id]
            display_name = item.container_name
            if display_name and display_name != "Unknown":
                self.selected_container_name = display_name
                logger.debug(f"Stored container name for refresh: {display_name}")
            
            # Immediately update basic info in UI
            self.container_name_label.configure(text=display_name)
            self.id_value.configure(text=container_id[:12] if container_id else "N/A")
            
            # Status if available
            if hasattr(item, 'status'):
                status = item.status
                status_display = status.title() if status else "Unknown"
                
                # Set status color
                if status == 'running':
                    status_color = SPOTIFY_COLORS["accent_green"]
                elif status in ['paused', 'restarting']:
                    status_color = SPOTIFY_COLORS["accent_orange"]
                else:
                    status_color = SPOTIFY_COLORS["accent_red"]
                    
                self.status_value.configure(text=status_display, text_color=status_color)
                
                # Update action buttons based on status
                self.update_action_buttons(status)
            else:
                self.status_value.configure(text="Loading...")
                
            # Show loading placeholders for other fields
            self.created_value.configure(text="Loading...")
            self.image_value.configure(text="Loading...")
            self.command_value.configure(text="Loading...")
            self.ports_value.configure(text="Loading...")
            
            # Loading placeholders for logs and inspect
            self.logs_text.configure(state="normal")
            self.logs_text.delete("1.0", "end")
            self.logs_text.insert("1.0", "Loading logs...")
            self.logs_text.configure(state="disabled")
            
            self.inspect_text.configure(state="normal")
            self.inspect_text.delete("1.0", "end")
            self.inspect_text.insert("1.0", "Loading container details...")
            self.inspect_text.configure(state="disabled")
        
        # Update selection in list
        for cid, item in self.container_items.items():
            item.set_selected(cid == container_id)
            
        if container_id is None:
            # Clear details
            self.container_name_label.configure(text="No container selected")
            self.status_value.configure(text="N/A")
            self.created_value.configure(text="N/A")
            self.id_value.configure(text="N/A")
            self.image_value.configure(text="N/A")
            self.command_value.configure(text="N/A")
            self.ports_value.configure(text="N/A")
            self.cpu_value.configure(text="0%")
            self.memory_value.configure(text="0 MB (0%)")
            self.network_value.configure(text="0 KB / 0 KB")
            self.cpu_progress.set(0)
            self.memory_progress.set(0)
            
            self.logs_text.configure(state="normal")
            self.logs_text.delete("1.0", "end")
            self.logs_text.configure(state="disabled")
            
            self.inspect_text.configure(state="normal")
            self.inspect_text.delete("1.0", "end")
            self.inspect_text.configure(state="disabled")
            
            # Disable action buttons
            self.update_action_buttons(None)
            return
            
        # Load container details in background thread
        threading.Thread(target=self.load_container_details, args=(container_id,), daemon=True).start()
        
    def load_container_details(self, container_id):
        """
        Load container details in a background thread.
        
        Args:
            container_id: Container ID
        """
        try:
            # Get container details
            container = self.docker_client.get_container(container_id)
            
            if not container:
                # Container might have been removed
                self.after(0, lambda: self.select_container(None))
                return
                
            # Get detailed inspection data
            try:
                inspection = self.docker_client.inspect_container(container_id)
            except (AttributeError, NotImplementedError):
                inspection = None
            
            # If we got detailed inspection data, use that instead
            if inspection and isinstance(inspection, dict) and 'Id' in inspection:
                container = inspection
                
            try:
                tail = int(self.logs_tail_var.get())
            except ValueError:
                tail = 100
            logs = self.docker_client.get_container_logs(container_id, tail=tail)
            
            # Update UI in main thread
            self.after(0, lambda: self.update_container_details(container, logs))
        except Exception as e:
            logger.error(f"Error loading container details: {e}")
            
    def update_container_details(self, container, logs):
        """
        Update container details in the UI.
        
        Args:
            container: Container details dictionary
            logs: Container logs
        """
        if not container:
            return
            
        if isinstance(container, str):
            # If container is a string, it's an error message
            logger.error(f"Error loading container: {container}")
            return
            
        # Ensure container is a dictionary
        if not isinstance(container, dict):
            logger.error(f"Container object is not a dictionary: {type(container)}")
            return
            
        container_id = container.get('Id', '')
        if not container_id or self.selected_container != container_id:
            return
            
        try:
            # Container name - handle different data formats
            if hasattr(self, 'selected_container_name') and self.selected_container_name:
                # Use saved name from previous refresh
                container_name = self.selected_container_name
                # Reset the saved name after using it
                self.selected_container_name = None
            else:
                # Get name from container object, handling different formats
                if 'Name' in container:
                    container_name = container.get('Name', 'Unknown').lstrip('/')
                elif 'Names' in container and container['Names'] and isinstance(container['Names'], list):
                    container_name = container['Names'][0].lstrip('/')
                else:
                    container_name = f"Container {container.get('Id', 'Unknown')[:12]}"
            
            self.container_name_label.configure(text=container_name)
            
            # Status
            status = container.get('State', {}).get('Status', 'unknown')
            status_display = status.title()
            
            # Set status color
            if status == 'running':
                status_color = SPOTIFY_COLORS["accent_green"]
            elif status in ['paused', 'restarting']:
                status_color = SPOTIFY_COLORS["accent_orange"]
            else:
                status_color = SPOTIFY_COLORS["accent_red"]
                
            self.status_value.configure(text=status_display, text_color=status_color)
            
            # Created time
            created = container.get('Created', 'Unknown')
            try:
                created_time = time.strftime('%Y-%m-%d %H:%M:%S', time.strptime(created.split('.')[0], '%Y-%m-%dT%H:%M:%S'))
            except:
                created_time = created
                
            self.created_value.configure(text=created_time)
            
            # Container ID
            container_id = container.get('Id', 'Unknown')[:12]
            self.id_value.configure(text=container_id)
            
            # Image
            image = container.get('Config', {}).get('Image', 'Unknown')
            self.image_value.configure(text=image)
            
            # Command
            command = container.get('Config', {}).get('Cmd', [])
            if command:
                if isinstance(command, list):
                    command = ' '.join(command)
                self.command_value.configure(text=command)
            else:
                self.command_value.configure(text="N/A")
                
            # Ports
            ports = container.get('NetworkSettings', {}).get('Ports', {})
            if ports:
                port_strings = []
                for container_port, host_bindings in ports.items():
                    if host_bindings:
                        for binding in host_bindings:
                            host_port = binding.get('HostPort', '')
                            port_strings.append(f"{host_port}:{container_port}")
                    else:
                        port_strings.append(container_port)
                        
                self.ports_value.configure(text=', '.join(port_strings))
            else:
                self.ports_value.configure(text="None")
                
            # Update metrics if available
            metrics = self.current_metrics.get(container.get('Id', ''), {})
            if metrics:
                # CPU usage
                cpu_percent = metrics.get('cpu_percent', 0.0)
                self.cpu_value.configure(
                    text=f"{cpu_percent:.1f}%",
                    text_color=self._get_resource_color(cpu_percent)
                )
                self.cpu_progress.set(cpu_percent / 100.0)
                
                # Memory usage
                memory_percent = metrics.get('memory_percent', 0.0)
                memory_usage = metrics.get('memory_usage', 0)
                memory_usage_mb = memory_usage / (1024 * 1024)
                
                self.memory_value.configure(
                    text=f"{memory_usage_mb:.1f} MB ({memory_percent:.1f}%)",
                    text_color=self._get_resource_color(memory_percent)
                )
                self.memory_progress.set(memory_percent / 100.0)
                
                # Network I/O
                network_rx = metrics.get('network_rx', 0)
                network_tx = metrics.get('network_tx', 0)
                
                # Format to KB, MB, or GB as appropriate
                def format_bytes(bytes_value):
                    if bytes_value < 1024:
                        return f"{bytes_value} B"
                    elif bytes_value < 1024 * 1024:
                        return f"{bytes_value / 1024:.1f} KB"
                    elif bytes_value < 1024 * 1024 * 1024:
                        return f"{bytes_value / (1024 * 1024):.1f} MB"
                    else:
                        return f"{bytes_value / (1024 * 1024 * 1024):.1f} GB"
                        
                self.network_value.configure(
                    text=f"{format_bytes(network_rx)} / {format_bytes(network_tx)}"
                )
            
            # Update logs tab
            self.logs_text.configure(state="normal")
            self.logs_text.delete("1.0", "end")
            self.logs_text.insert("1.0", logs)
            self.logs_text.configure(state="disabled")
            
            # Update inspect tab
            import json
            self.inspect_text.configure(state="normal")
            self.inspect_text.delete("1.0", "end")
            self.inspect_text.insert("1.0", json.dumps(container, indent=2))
            self.inspect_text.configure(state="disabled")
            
            # Update action buttons
            self.update_action_buttons(status)
            
        except Exception as e:
            logger.error(f"Error updating container details: {e}")
            
    def update_action_buttons(self, status):
        """
        Update action buttons based on container status.
        
        Args:
            status: Container status or None if no container selected
        """
        if status is None:
            # No container selected
            self.start_button.configure(state="disabled")
            self.stop_button.configure(state="disabled")
            self.restart_button.configure(state="disabled")
            self.delete_button.configure(state="disabled")
            return
            
        # Enable/disable buttons based on status
        if status == 'running':
            self.start_button.configure(state="disabled")
            self.stop_button.configure(state="normal")
            self.restart_button.configure(state="normal")
            self.delete_button.configure(state="normal")
        elif status in ['created', 'exited', 'dead']:
            self.start_button.configure(state="normal")
            self.stop_button.configure(state="disabled")
            self.restart_button.configure(state="normal")
            self.delete_button.configure(state="normal")
        elif status in ['paused']:
            self.start_button.configure(state="normal")
            self.stop_button.configure(state="normal")
            self.restart_button.configure(state="normal")
            self.delete_button.configure(state="normal")
        else:
            # Unknown status, disable all to be safe
            self.start_button.configure(state="disabled")
            self.stop_button.configure(state="disabled")
            self.restart_button.configure(state="disabled")
            self.delete_button.configure(state="normal")
            
    def start_container(self):
        """Start the selected container."""
        if not self.selected_container:
            return
            
        threading.Thread(target=self._start_container_thread, daemon=True).start()
        
    def _start_container_thread(self):
        """Start container in a background thread."""
        try:
            # Disable buttons during operation
            self.after(0, lambda: self.update_action_buttons(None))
            
            # Start container
            success = self.docker_client.start_container(self.selected_container)
            
            if success:
                # Refresh container details
                self.after(500, self.refresh)  # Wait a bit for Docker to update
            else:
                messagebox.showerror("Error", "Failed to start container")
                self.after(0, self.refresh)
        except Exception as e:
            logger.error(f"Error starting container: {e}")
            self.after(0, lambda: messagebox.showerror("Error", f"Failed to start container: {e}"))
            self.after(0, self.refresh)
            
    def stop_container(self):
        """Stop the selected container."""
        if not self.selected_container:
            return
            
        threading.Thread(target=self._stop_container_thread, daemon=True).start()
        
    def _stop_container_thread(self):
        """Stop container in a background thread."""
        try:
            # Disable buttons during operation
            self.after(0, lambda: self.update_action_buttons(None))
            
            # Stop container
            success = self.docker_client.stop_container(self.selected_container)
            
            if success:
                # Refresh container details
                self.after(500, self.refresh)  # Wait a bit for Docker to update
            else:
                messagebox.showerror("Error", "Failed to stop container")
                self.after(0, self.refresh)
        except Exception as e:
            logger.error(f"Error stopping container: {e}")
            self.after(0, lambda: messagebox.showerror("Error", f"Failed to stop container: {e}"))
            self.after(0, self.refresh)
            
    def restart_container(self):
        """Restart the selected container."""
        if not self.selected_container:
            return
            
        threading.Thread(target=self._restart_container_thread, daemon=True).start()
        
    def _restart_container_thread(self):
        """Restart container in a background thread."""
        try:
            # Disable buttons during operation
            self.after(0, lambda: self.update_action_buttons(None))
            
            # Restart container
            success = self.docker_client.restart_container(self.selected_container)
            
            if success:
                # Refresh container details
                self.after(1000, self.refresh)  # Wait a bit longer for restart
            else:
                messagebox.showerror("Error", "Failed to restart container")
                self.after(0, self.refresh)
        except Exception as e:
            logger.error(f"Error restarting container: {e}")
            self.after(0, lambda: messagebox.showerror("Error", f"Failed to restart container: {e}"))
            self.after(0, self.refresh)
            
    def delete_container(self):
        """Delete the selected container."""
        if not self.selected_container:
            return
            
        # Confirm deletion
        if not messagebox.askyesno("Confirm Delete", 
                                 "Are you sure you want to delete this container?\nThis action cannot be undone."):
            return
            
        # Ask if should force delete
        force = False
        if messagebox.askyesno("Force Delete", 
                             "Force delete if the container is running?"):
            force = True
            
        threading.Thread(target=self._delete_container_thread, args=(force,), daemon=True).start()
        
    def _delete_container_thread(self, force: bool):
        """
        Delete container in a background thread.
        
        Args:
            force: Whether to force deletion of a running container
        """
        try:
            # Disable buttons during operation
            self.after(0, lambda: self.update_action_buttons(None))
            
            # Delete container
            success = self.docker_client.remove_container(self.selected_container, force=force)
            
            if success:
                # Clear selection and refresh
                self.after(0, lambda: self.select_container(None))
                self.after(500, self.refresh)
            else:
                messagebox.showerror("Error", "Failed to delete container")
                self.after(0, self.refresh)
        except Exception as e:
            logger.error(f"Error deleting container: {e}")
            self.after(0, lambda: messagebox.showerror("Error", f"Failed to delete container: {e}"))
            self.after(0, self.refresh)
            
    def refresh_logs(self):
        """Refresh logs for the selected container."""
        if not self.selected_container:
            return
            
        self.load_container_details(self.selected_container)
        
    def update_metrics(self, metrics: Dict[str, Dict[str, Any]]):
        """
        Update container metrics.
        
        Args:
            metrics: Dictionary of container metrics
        """
        try:
            # Store current metrics
            self.current_metrics = metrics
            
            # Update container items with new metrics
            for container_id, container_metrics in metrics.items():
                if container_id in self.container_items:
                    self.container_items[container_id].update_metrics(container_metrics)
                    
            # Update selected container details
            if self.selected_container and self.selected_container in metrics:
                container = self.docker_client.get_container(self.selected_container)
                self.update_container_details(container, self.logs_text.get("1.0", "end"))
                
        except Exception as e:
            logger.error(f"Error updating metrics: {e}")
            
    def _get_resource_color(self, value: float) -> str:
        """
        Get color based on resource usage value.
        
        Args:
            value: Resource usage percentage
            
        Returns:
            Color string
        """
        if value < 50:
            return SPOTIFY_COLORS["accent_green"]
        elif value < 80:
            return SPOTIFY_COLORS["accent_orange"]
        else:
            return SPOTIFY_COLORS["accent_red"]
            
    def apply_resource_limits(self):
        """Apply resource limits to the selected container."""
        if not self.selected_container:
            messagebox.showinfo("No Container Selected", "Please select a container first.")
            return
        
        try:
            # Get limit values
            cpu_limit = float(self.cpu_limit_var.get())
            memory_limit = float(self.memory_limit_var.get())
            
            # Validate limit values
            if cpu_limit < 0 or cpu_limit > 100 or memory_limit < 0 or memory_limit > 100:
                messagebox.showerror("Invalid Limits", 
                                     "Limits must be between 0 and 100 percent.")
                return
                
            # Get alert manager from parent
            alert_manager = self.parent.alert_manager
            
            # Set container-specific thresholds
            alert_manager.set_container_threshold(self.selected_container, 'cpu_percent', cpu_limit)
            alert_manager.set_container_threshold(self.selected_container, 'memory_percent', memory_limit)
            
            # Confirmation message
            container_name = self.container_name_label.cget("text")
            messagebox.showinfo("Limits Applied", 
                               f"Resource limits for '{container_name}' have been updated.\n\n"
                               f"CPU Alert: {cpu_limit}%\n"
                               f"Memory Alert: {memory_limit}%")
            
        except ValueError:
            messagebox.showerror("Invalid Input", 
                                "Please enter valid numbers for resource limits.")
        except Exception as e:
            logger.error(f"Error applying resource limits: {e}")
            messagebox.showerror("Error", f"Failed to apply resource limits: {str(e)}")


class ContainerListItem(ctk.CTkFrame):
    """
    Container list item widget for displaying container in the list.
    """
    def __init__(self, parent, container: Dict[str, Any], metrics: Dict[str, Any] = None, 
                command: Callable = None):
        """
        Initialize container list item.
        
        Args:
            parent: Parent widget
            container: Container dictionary
            metrics: Container metrics dictionary
            command: Callback when item is clicked
        """
        super().__init__(
            parent,
            fg_color=scale_color(SPOTIFY_COLORS["card_background"], 1.1),
            corner_radius=5,
            height=40
        )
        
        self.container = container
        self.metrics = metrics or {}
        self.command = command
        self.selected = False
        self.container_name = ""  # Store container name separately for easy reference
        
        # Create UI
        self.create_ui()
        
        # Apply data
        self.update(container, metrics)
        
        # Force window to update properly to avoid black squares
        self.update_idletasks()
        
        # Bind click event
        self.bind("<Button-1>", self._on_click)
        for child in self.winfo_children():
            child.bind("<Button-1>", self._on_click)
        
    def create_ui(self):
        """Create and setup the user interface."""
        self.grid_columnconfigure(1, weight=1)
        
        # Status indicator
        self.status_indicator = StatusIndicator(self, size=8)
        self.status_indicator.grid(row=0, column=0, padx=(10, 5), pady=10)
        
        # Container name
        self.name_label = ctk.CTkLabel(
            self,
            text="",
            font=("Helvetica", 12),
            text_color=SPOTIFY_COLORS["text_bright"],
            anchor="w"
        )
        self.name_label.grid(row=0, column=1, sticky="ew", padx=5, pady=10)
        
        # Container ID (short)
        self.id_label = ctk.CTkLabel(
            self,
            text="",
            font=("Helvetica", 10),
            text_color=SPOTIFY_COLORS["text_subtle"],
            width=70
        )
        self.id_label.grid(row=0, column=2, padx=5, pady=10)
        
    def update(self, container: Dict[str, Any], metrics: Dict[str, Any] = None):
        """
        Update container item with new data.
        
        Args:
            container: Container dictionary
            metrics: Container metrics dictionary
        """
        self.container = container
        if metrics:
            self.metrics = metrics
            
        # Container name
        container_name = container.get('Names', [''])[0].lstrip('/')
        if container_name:
            self.container_name = container_name  # Store for reference
        self.name_label.configure(text=container_name)
        
        # Container ID (short)
        container_id = container.get('Id', '')[:12]
        self.id_label.configure(text=container_id)
        
        # Status
        status = container.get('State', '').lower()
        if status == 'running':
            self.status_indicator.set_status('green')
        elif status in ['paused', 'restarting']:
            self.status_indicator.set_status('yellow')
        else:
            self.status_indicator.set_status('red')
            
    def update_metrics(self, metrics: Dict[str, Any]):
        """
        Update container metrics.
        
        Args:
            metrics: Container metrics dictionary
        """
        if not metrics:
            return
            
        self.metrics = metrics
        
    def set_selected(self, selected: bool):
        """
        Set whether this item is selected.
        
        Args:
            selected: Whether the item is selected
        """
        if self.selected == selected:
            return
            
        self.selected = selected
        
        if selected:
            self.configure(fg_color=SPOTIFY_COLORS["accent"])
            self.name_label.configure(font=("Helvetica", 12, "bold"))
        else:
            self.configure(fg_color=scale_color(SPOTIFY_COLORS["card_background"], 1.1))
            self.name_label.configure(font=("Helvetica", 12))
            
    def _on_click(self, event):
        """
        Handle click event.
        
        Args:
            event: Click event
        """
        if self.command:
            self.command()
