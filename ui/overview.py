"""
Overview dashboard frame for Dockify.
"""
import logging
import time
import tkinter as tk
from tkinter import ttk
from typing import Dict, List, Any, Optional, Callable
import threading

import customtkinter as ctk

from core.docker_client import DockerClient
from core.monitor import ContainerMonitor
from core.alerts import AlertManager
from ui.components import GradientFrame, MetricCard, StatusIndicator
from utils.theme import SPOTIFY_COLORS, lighten_color, scale_color

logger = logging.getLogger('dockify.ui.overview')

class OverviewFrame(ctk.CTkFrame):
    """
    Overview dashboard showing summary of container metrics and system status.
    """
    def __init__(self, parent, docker_client: Any, 
                 container_monitor: ContainerMonitor,
                 alert_manager: AlertManager):
        """
        Initialize the overview dashboard.
        
        Args:
            parent: Parent widget
            docker_client: Docker client instance
            container_monitor: Container monitor instance
            alert_manager: Alert manager instance
        """
        super().__init__(parent, corner_radius=0, fg_color=SPOTIFY_COLORS["background"])
        self.parent = parent
        self.docker_client = docker_client
        self.container_monitor = container_monitor
        self.alert_manager = alert_manager
        
        # Container for last received metrics
        self.current_metrics: Dict[str, Dict[str, Any]] = {}
        self.system_info: Dict[str, Any] = {}
        
        # Create UI
        self.create_ui()
        
        # Initial data load
        self.refresh()
        
    def create_ui(self):
        """Create and setup the user interface."""
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)  # Header
        self.grid_rowconfigure(1, weight=0)  # System summary
        self.grid_rowconfigure(2, weight=1)  # Container list
        self.grid_rowconfigure(3, weight=0)  # Active alerts
        
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
            text="Overview",
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
        
        # System summary section
        self.system_frame = ctk.CTkFrame(
            self,
            fg_color=SPOTIFY_COLORS["card_background"],
            corner_radius=10
        )
        self.system_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 20))
        
        # Create metric cards
        self.system_frame.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="metrics")
        
        # Docker engine status card
        self.docker_status_card = MetricCard(
            self.system_frame,
            title="Docker Engine",
            value="Checking...",
            icon="docker",
            progress=0,
            color=SPOTIFY_COLORS["accent"]
        )
        self.docker_status_card.grid(row=0, column=0, padx=10, pady=10)
        
        # Container count card
        self.container_count_card = MetricCard(
            self.system_frame,
            title="Containers",
            value="0",
            subtitle="0 running",
            icon="cube",
            progress=0,
            color=SPOTIFY_COLORS["accent_green"]
        )
        self.container_count_card.grid(row=0, column=1, padx=10, pady=10)
        
        # System CPU card
        self.cpu_card = MetricCard(
            self.system_frame,
            title="System CPU",
            value="0%",
            icon="cpu",
            progress=0,
            color=SPOTIFY_COLORS["accent_orange"]
        )
        self.cpu_card.grid(row=0, column=2, padx=10, pady=10)
        
        # System memory card
        self.memory_card = MetricCard(
            self.system_frame,
            title="System Memory",
            value="0 MB",
            subtitle="0%",
            icon="memory",
            progress=0,
            color=SPOTIFY_COLORS["accent_purple"]
        )
        self.memory_card.grid(row=0, column=3, padx=10, pady=10)
        
        # Containers section
        self.containers_frame = ctk.CTkFrame(
            self,
            fg_color=SPOTIFY_COLORS["card_background"],
            corner_radius=10
        )
        self.containers_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0, 20))
        
        # Section title
        self.containers_label = ctk.CTkLabel(
            self.containers_frame,
            text="Container Status",
            font=("Helvetica", 16, "bold"),
            text_color=SPOTIFY_COLORS["text_bright"]
        )
        self.containers_label.pack(anchor="w", padx=15, pady=10)
        
        # Container list
        self.container_list_frame = ctk.CTkScrollableFrame(
            self.containers_frame,
            fg_color="transparent"
        )
        self.container_list_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Container items will be added dynamically
        self.container_items = {}
        
        # Alerts section
        self.alerts_frame = ctk.CTkFrame(
            self,
            fg_color=SPOTIFY_COLORS["card_background"],
            corner_radius=10,
            height=120
        )
        self.alerts_frame.grid(row=3, column=0, sticky="ew", padx=20, pady=(0, 20))
        self.alerts_frame.grid_propagate(False)
        
        # Section title
        self.alerts_label = ctk.CTkLabel(
            self.alerts_frame,
            text="Active Alerts",
            font=("Helvetica", 16, "bold"),
            text_color=SPOTIFY_COLORS["text_bright"]
        )
        self.alerts_label.pack(anchor="w", padx=15, pady=10)
        
        # Alert list
        self.alert_list_frame = ctk.CTkScrollableFrame(
            self.alerts_frame,
            fg_color="transparent"
        )
        self.alert_list_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # No alerts message
        self.no_alerts_label = ctk.CTkLabel(
            self.alert_list_frame,
            text="No active alerts",
            font=("Helvetica", 12),
            text_color=SPOTIFY_COLORS["text_subtle"]
        )
        self.no_alerts_label.pack(pady=10)
        
        # Alert items will be added dynamically
        self.alert_items = {}
        
    def refresh(self):
        """Refresh all data on the overview page."""
        try:
            # Update system info
            threading.Thread(target=self.load_system_info, daemon=True).start()
            
            # Update container list
            threading.Thread(target=self.load_containers, daemon=True).start()
            
            # Update alerts
            self.update_alerts()
            
            # Update refresh time
            self.refresh_label.configure(text=f"Last updated: {time.strftime('%H:%M:%S')}")
        except Exception as e:
            logger.error(f"Error refreshing overview: {e}")
            
    def load_system_info(self):
        """Load system information in a background thread."""
        try:
            # Get Docker info
            docker_info = self.docker_client.get_docker_info()
            
            # Get system metrics
            system_metrics = self.container_monitor.get_system_metrics()
            
            # Store system info
            self.system_info = {
                "docker_info": docker_info,
                "system_metrics": system_metrics
            }
            
            # Update UI
            self.after(0, self.update_system_info)
        except Exception as e:
            logger.error(f"Error loading system info: {e}")
            
    def update_system_info(self):
        """Update system information cards."""
        try:
            docker_info = self.system_info.get("docker_info", {})
            system_metrics = self.system_info.get("system_metrics", {})
            
            # Remove debug prints now that we've fixed the issue
            
            # Update Docker engine status
            docker_status = "Running" if docker_info.get("ServerVersion") else "Unavailable"
            docker_version = docker_info.get("ServerVersion", "Unknown")
            self.docker_status_card.update_values(
                value=docker_status,
                subtitle=f"v{docker_version}" if docker_status == "Running" else "",
                progress=100 if docker_status == "Running" else 0
            )
            
            # Update container count
            containers_data = docker_info.get("Containers", [])
            total_containers = len(containers_data) if isinstance(containers_data, list) else containers_data if isinstance(containers_data, int) else 0
            
            # Count running containers
            running_containers = 0
            if hasattr(self, 'current_metrics') and self.current_metrics:
                running_containers = len([c for c in self.current_metrics.values() 
                                         if c.get("status") == "running"])
            
            self.container_count_card.update_values(
                value=str(total_containers),
                subtitle=f"{running_containers} running",
                progress=(running_containers / total_containers * 100) if total_containers > 0 else 0
            )
            
            # Update CPU usage
            cpu_percent = system_metrics.get("cpu_percent", 0)
            self.cpu_card.update_values(
                value=f"{cpu_percent:.1f}%",
                progress=cpu_percent
            )
            
            # Update memory usage
            memory_percent = system_metrics.get("memory_percent", 0)
            memory_used = system_metrics.get("memory_total", 0) - system_metrics.get("memory_available", 0)
            memory_total = system_metrics.get("memory_total", 0)
            
            # Convert to MB
            memory_used_mb = memory_used / (1024 * 1024)
            memory_total_mb = memory_total / (1024 * 1024)
            
            # Or GB if large enough
            if memory_total_mb > 1024:
                memory_used_gb = memory_used_mb / 1024
                memory_total_gb = memory_total_mb / 1024
                memory_text = f"{memory_used_gb:.1f}/{memory_total_gb:.1f} GB"
            else:
                memory_text = f"{memory_used_mb:.0f}/{memory_total_mb:.0f} MB"
                
            self.memory_card.update_values(
                value=memory_text,
                subtitle=f"{memory_percent:.1f}%",
                progress=memory_percent
            )
            
        except Exception as e:
            logger.error(f"Error updating system info: {e}")
            
    def load_containers(self):
        """Load container list in a background thread."""
        try:
            # Get containers
            containers = self.docker_client.list_containers()
            
            # Update UI
            self.after(0, lambda: self.update_container_list(containers))
        except Exception as e:
            logger.error(f"Error loading containers: {e}")
            
    def update_container_list(self, containers):
        """
        Update the container list.
        
        Args:
            containers: List of container dictionaries
        """
        try:
            # Track existing container IDs
            existing_ids = set(self.container_items.keys())
            new_ids = set()
            
            # Add or update containers
            for container in containers:
                container_id = container.get('Id', '')
                new_ids.add(container_id)
                
                # Get container name
                container_name = container.get('Names', [''])[0].lstrip('/')
                
                # Get metrics if available
                metrics = self.current_metrics.get(container_id, {})
                
                if container_id in existing_ids:
                    # Update existing container
                    self.container_items[container_id].update(container, metrics)
                else:
                    # Create new container item
                    container_item = ContainerItem(
                        self.container_list_frame, 
                        container, 
                        metrics
                    )
                    container_item.pack(fill="x", padx=5, pady=3)
                    self.container_items[container_id] = container_item
                    
            # Remove containers that no longer exist
            for container_id in existing_ids - new_ids:
                self.container_items[container_id].destroy()
                del self.container_items[container_id]
                
            # Show message if no containers
            if not containers:
                if not hasattr(self, 'no_containers_label'):
                    self.no_containers_label = ctk.CTkLabel(
                        self.container_list_frame,
                        text="No containers found",
                        font=("Helvetica", 12),
                        text_color=SPOTIFY_COLORS["text_subtle"]
                    )
                    self.no_containers_label.pack(pady=10)
            elif hasattr(self, 'no_containers_label') and self.no_containers_label.winfo_exists():
                self.no_containers_label.destroy()
                
        except Exception as e:
            logger.error(f"Error updating container list: {e}")
            
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
                    
            # Update system metrics (CPU and memory)
            system_metrics = self.container_monitor.get_system_metrics()
            if system_metrics:
                self.system_info["system_metrics"] = system_metrics
                self.update_system_info()
                
            # Update last refresh time
            self.refresh_label.configure(text=f"Last updated: {time.strftime('%H:%M:%S')}")
            
        except Exception as e:
            logger.error(f"Error updating metrics: {e}")
            
    def update_alerts(self):
        """Update the alerts section."""
        try:
            active_alerts = self.alert_manager.get_active_alerts()
            
            # Track existing alert IDs
            existing_ids = set(self.alert_items.keys())
            new_ids = set(active_alerts.keys())
            
            # Add or update alerts
            for alert_id, alert in active_alerts.items():
                if alert_id in existing_ids:
                    # Update existing alert
                    self.alert_items[alert_id].update(alert)
                else:
                    # Create new alert item
                    alert_item = AlertItem(
                        self.alert_list_frame,
                        alert
                    )
                    alert_item.pack(fill="x", padx=5, pady=3)
                    self.alert_items[alert_id] = alert_item
                    
            # Remove alerts that are no longer active
            for alert_id in existing_ids - new_ids:
                self.alert_items[alert_id].destroy()
                del self.alert_items[alert_id]
                
            # Show/hide no alerts message
            if not active_alerts:
                self.no_alerts_label.pack(pady=10)
            else:
                self.no_alerts_label.pack_forget()
                
        except Exception as e:
            logger.error(f"Error updating alerts: {e}")


class ContainerItem(ctk.CTkFrame):
    """
    Container item widget for displaying container information.
    """
    def __init__(self, parent, container: Dict[str, Any], metrics: Dict[str, Any] = None):
        """
        Initialize container item.
        
        Args:
            parent: Parent widget
            container: Container dictionary
            metrics: Container metrics dictionary
        """
        super().__init__(
            parent,
            fg_color=scale_color(SPOTIFY_COLORS["card_background"], 1.1),
            corner_radius=5,
            height=45
        )
        
        self.container = container
        self.metrics = metrics or {}
        
        # Create UI
        self.create_ui()
        
        # Apply data
        self.update(container, metrics)
        
    def create_ui(self):
        """Create and setup the user interface."""
        self.grid_columnconfigure(1, weight=1)
        
        # Status indicator
        self.status_indicator = StatusIndicator(self, size=10)
        self.status_indicator.grid(row=0, column=0, padx=(10, 5), pady=10)
        
        # Container name
        self.name_label = ctk.CTkLabel(
            self,
            text="",
            font=("Helvetica", 12, "bold"),
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
        
        # CPU usage
        self.cpu_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.cpu_frame.grid(row=0, column=3, padx=5, pady=10)
        
        self.cpu_label = ctk.CTkLabel(
            self.cpu_frame,
            text="CPU:",
            font=("Helvetica", 10),
            text_color=SPOTIFY_COLORS["text_subtle"],
            width=35
        )
        self.cpu_label.pack(side="left")
        
        self.cpu_value = ctk.CTkLabel(
            self.cpu_frame,
            text="0%",
            font=("Helvetica", 10, "bold"),
            text_color=SPOTIFY_COLORS["accent_green"],
            width=40
        )
        self.cpu_value.pack(side="left")
        
        # Memory usage
        self.memory_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.memory_frame.grid(row=0, column=4, padx=5, pady=10)
        
        self.memory_label = ctk.CTkLabel(
            self.memory_frame,
            text="RAM:",
            font=("Helvetica", 10),
            text_color=SPOTIFY_COLORS["text_subtle"],
            width=35
        )
        self.memory_label.pack(side="left")
        
        self.memory_value = ctk.CTkLabel(
            self.memory_frame,
            text="0%",
            font=("Helvetica", 10, "bold"),
            text_color=SPOTIFY_COLORS["accent_purple"],
            width=40
        )
        self.memory_value.pack(side="left")
        
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
            
        # Update metrics
        self.update_metrics(self.metrics)
        
    def update_metrics(self, metrics: Dict[str, Any]):
        """
        Update container metrics.
        
        Args:
            metrics: Container metrics dictionary
        """
        if not metrics:
            return
            
        self.metrics = metrics
        
        # CPU usage
        cpu_percent = metrics.get('cpu_percent', 0.0)
        self.cpu_value.configure(
            text=f"{cpu_percent:.1f}%",
            text_color=self._get_resource_color(cpu_percent)
        )
        
        # Memory usage
        memory_percent = metrics.get('memory_percent', 0.0)
        self.memory_value.configure(
            text=f"{memory_percent:.1f}%",
            text_color=self._get_resource_color(memory_percent)
        )
        
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


class AlertItem(ctk.CTkFrame):
    """
    Alert item widget for displaying alert information.
    """
    def __init__(self, parent, alert: Dict[str, Any]):
        """
        Initialize alert item.
        
        Args:
            parent: Parent widget
            alert: Alert dictionary
        """
        super().__init__(
            parent,
            fg_color=scale_color(SPOTIFY_COLORS["card_background"], 1.1),
            corner_radius=5,
            height=40
        )
        
        self.alert = alert
        
        # Create UI
        self.create_ui()
        
        # Apply data
        self.update(alert)
        
    def create_ui(self):
        """Create and setup the user interface."""
        self.grid_columnconfigure(1, weight=1)
        
        # Alert icon
        self.alert_icon = ctk.CTkLabel(
            self,
            text="⚠️",
            font=("Helvetica", 14),
            text_color=SPOTIFY_COLORS["accent_orange"],
            width=20
        )
        self.alert_icon.grid(row=0, column=0, padx=(10, 5), pady=10)
        
        # Container name and metric
        self.info_label = ctk.CTkLabel(
            self,
            text="",
            font=("Helvetica", 12),
            text_color=SPOTIFY_COLORS["text_bright"],
            anchor="w"
        )
        self.info_label.grid(row=0, column=1, sticky="ew", padx=5, pady=10)
        
        # Value
        self.value_label = ctk.CTkLabel(
            self,
            text="",
            font=("Helvetica", 12, "bold"),
            text_color=SPOTIFY_COLORS["accent_red"]
        )
        self.value_label.grid(row=0, column=2, padx=10, pady=10)
        
    def update(self, alert: Dict[str, Any]):
        """
        Update alert item with new data.
        
        Args:
            alert: Alert dictionary
        """
        self.alert = alert
        
        # Alert details
        container_name = alert.get('container_name', 'Unknown')
        metric = alert.get('metric', 'Unknown')
        threshold = alert.get('threshold', 0.0)
        value = alert.get('value', 0.0)
        
        # Format metric name for display
        if metric == 'cpu_percent':
            metric_name = 'CPU'
        elif metric == 'memory_percent':
            metric_name = 'Memory'
        else:
            metric_name = metric.replace('_', ' ').title()
            
        # Update labels
        self.info_label.configure(text=f"{container_name}: {metric_name} exceeds {threshold:.1f}%")
        self.value_label.configure(text=f"{value:.1f}%")
        
        # Set icon color based on severity
        if value > threshold * 1.5:
            self.alert_icon.configure(text_color=SPOTIFY_COLORS["accent_red"])
        elif value > threshold * 1.2:
            self.alert_icon.configure(text_color=SPOTIFY_COLORS["accent_orange"])
        else:
            self.alert_icon.configure(text_color=SPOTIFY_COLORS["accent_yellow"])
