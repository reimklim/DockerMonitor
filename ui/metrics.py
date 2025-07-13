"""
Metrics visualization frame for Dockify.
"""
import logging
import time
import json
import tkinter as tk
from tkinter import ttk
from typing import Dict, List, Any, Optional, Callable, Tuple
import threading
import datetime

import customtkinter as ctk
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from core.docker_client import DockerClient
from core.monitor import ContainerMonitor
from ui.components import GradientFrame, ActionButton, DropdownSelector
from utils.theme import SPOTIFY_COLORS, lighten_color, scale_color

logger = logging.getLogger('dockify.ui.metrics')

class MetricsFrame(ctk.CTkFrame):
    """
    Metrics visualization screen for analyzing container performance over time.
    """
    def __init__(self, parent, docker_client: Any, container_monitor: ContainerMonitor):
        """
        Initialize the metrics visualization screen.
        
        Args:
            parent: Parent widget
            docker_client: Docker client instance
            container_monitor: Container monitor instance
        """
        super().__init__(parent, corner_radius=0, fg_color=SPOTIFY_COLORS["background"])
        self.parent = parent
        self.docker_client = docker_client
        self.container_monitor = container_monitor
        
        # Currently selected container
        self.selected_container: Optional[str] = None
        
        # Current metrics data
        self.current_metrics: Dict[str, Dict[str, Any]] = {}
        
        # Plot HTML
        self.cpu_plot_html: str = ""
        self.memory_plot_html: str = ""
        
        # Create UI
        self.create_ui()
        
        # Initial data load
        self.refresh()
        
    def create_ui(self):
        """Create and setup the user interface."""
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)  # Header
        self.grid_rowconfigure(1, weight=0)  # Controls
        self.grid_rowconfigure(2, weight=1)  # Charts
        
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
            text="Metrics",
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
        
        # Controls section
        self.controls_frame = ctk.CTkFrame(
            self,
            fg_color=SPOTIFY_COLORS["card_background"],
            corner_radius=10,
            height=70
        )
        self.controls_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 20))
        self.controls_frame.grid_propagate(False)
        
        # Container selection
        self.container_selector_label = ctk.CTkLabel(
            self.controls_frame,
            text="Container:",
            font=("Helvetica", 12),
            text_color=SPOTIFY_COLORS["text_subtle"]
        )
        self.container_selector_label.place(relx=0.02, rely=0.5, anchor="w")
        
        self.container_var = tk.StringVar(value="Select a container")
        self.container_selector = DropdownSelector(
            self.controls_frame,
            variable=self.container_var,
            values=["Select a container"],
            command=self.on_container_selected,
            width=250,
        )
        self.container_selector.place(relx=0.15, rely=0.5, anchor="w")
        
        # Time range selection
        self.time_range_label = ctk.CTkLabel(
            self.controls_frame,
            text="Time range:",
            font=("Helvetica", 12),
            text_color=SPOTIFY_COLORS["text_subtle"]
        )
        self.time_range_label.place(relx=0.45, rely=0.5, anchor="w")
        
        self.time_range_var = tk.StringVar(value="Last 5 minutes")
        self.time_range_selector = DropdownSelector(
            self.controls_frame,
            variable=self.time_range_var,
            values=["Last 5 minutes", "Last 15 minutes", "Last hour", "All"],
            command=self.refresh_graphs,
            width=150,
        )
        self.time_range_selector.place(relx=0.55, rely=0.5, anchor="w")
        
        # Refresh button
        self.refresh_button = ctk.CTkButton(
            self.controls_frame,
            text="Refresh",
            font=("Helvetica", 12),
            fg_color=SPOTIFY_COLORS["accent_green"],
            hover_color=lighten_color(SPOTIFY_COLORS["accent_green"], 0.1),
            text_color=SPOTIFY_COLORS["text_bright"],
            width=100,
            command=self.refresh_graphs
        )
        self.refresh_button.place(relx=0.95, rely=0.5, anchor="e")
        
        # Charts section
        self.charts_frame = ctk.CTkFrame(
            self,
            fg_color="transparent"
        )
        self.charts_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=0)
        self.charts_frame.grid_columnconfigure(0, weight=1)
        self.charts_frame.grid_rowconfigure(0, weight=1)  # CPU chart
        self.charts_frame.grid_rowconfigure(1, weight=1)  # Memory chart
        
        # CPU usage chart
        self.cpu_chart_frame = ctk.CTkFrame(
            self.charts_frame,
            fg_color=SPOTIFY_COLORS["card_background"],
            corner_radius=10
        )
        self.cpu_chart_frame.grid(row=0, column=0, sticky="nsew", padx=0, pady=(0, 10))
        
        # CPU chart title
        self.cpu_chart_title = ctk.CTkLabel(
            self.cpu_chart_frame,
            text="CPU Usage (%)",
            font=("Helvetica", 16, "bold"),
            text_color=SPOTIFY_COLORS["text_bright"]
        )
        self.cpu_chart_title.pack(anchor="w", padx=15, pady=10)
        
        # CPU chart placeholder
        self.cpu_chart_placeholder = ctk.CTkLabel(
            self.cpu_chart_frame,
            text="Select a container to view CPU metrics",
            font=("Helvetica", 14),
            text_color=SPOTIFY_COLORS["text_subtle"]
        )
        self.cpu_chart_placeholder.pack(expand=True, fill="both", padx=15, pady=15)
        
        # Memory usage chart
        self.memory_chart_frame = ctk.CTkFrame(
            self.charts_frame,
            fg_color=SPOTIFY_COLORS["card_background"],
            corner_radius=10
        )
        self.memory_chart_frame.grid(row=1, column=0, sticky="nsew", padx=0, pady=(10, 0))
        
        # Memory chart title
        self.memory_chart_title = ctk.CTkLabel(
            self.memory_chart_frame,
            text="Memory Usage (%)",
            font=("Helvetica", 16, "bold"),
            text_color=SPOTIFY_COLORS["text_bright"]
        )
        self.memory_chart_title.pack(anchor="w", padx=15, pady=10)
        
        # Memory chart placeholder
        self.memory_chart_placeholder = ctk.CTkLabel(
            self.memory_chart_frame,
            text="Select a container to view memory metrics",
            font=("Helvetica", 14),
            text_color=SPOTIFY_COLORS["text_subtle"]
        )
        self.memory_chart_placeholder.pack(expand=True, fill="both", padx=15, pady=15)
        
    def refresh(self):
        """Refresh container list and graphs."""
        try:
            # Update container selector
            threading.Thread(target=self.load_containers, daemon=True).start()
            
            # Update graphs if container is selected
            if self.selected_container:
                self.refresh_graphs()
                
            # Update refresh time
            self.refresh_label.configure(text=f"Last updated: {time.strftime('%H:%M:%S')}")
        except Exception as e:
            logger.error(f"Error refreshing metrics view: {e}")
            
    def load_containers(self):
        """Load container list in a background thread."""
        try:
            # Get containers
            containers = self.docker_client.list_containers()
            
            # Update UI in main thread
            self.after(0, lambda: self.update_container_selector(containers))
        except Exception as e:
            logger.error(f"Error loading containers: {e}")
            
    def update_container_selector(self, containers):
        """
        Update the container selector dropdown.
        
        Args:
            containers: List of container dictionaries
        """
        try:
            # Create container name to ID mapping
            container_map = {}
            
            for container in containers:
                container_id = container.get('Id', '')
                container_name = container.get('Names', [''])[0].lstrip('/')
                
                if container_name:
                    display_name = f"{container_name} ({container_id[:12]})"
                    container_map[display_name] = container_id
                    
            # Update dropdown values
            if container_map:
                container_names = list(container_map.keys())
                container_names.sort()
                
                self.container_selector.configure(values=container_names)
                
                # If no container is selected, select the first one
                if not self.selected_container and container_names:
                    self.container_var.set(container_names[0])
                    self.selected_container = container_map[container_names[0]]
                    self.refresh_graphs()
                else:
                    # Find and select the current container in the new list
                    current_display_name = self.container_var.get()
                    
                    # If the current selection is not in the new list, reset selection
                    if current_display_name not in container_map:
                        # Try to find container by ID
                        found = False
                        for display_name, container_id in container_map.items():
                            if container_id == self.selected_container:
                                self.container_var.set(display_name)
                                found = True
                                break
                                
                        # If not found, reset selection
                        if not found:
                            if container_names:
                                self.container_var.set(container_names[0])
                                self.selected_container = container_map[container_names[0]]
                            else:
                                self.container_var.set("Select a container")
                                self.selected_container = None
                                
                            self.refresh_graphs()
            else:
                # No containers available
                self.container_selector.configure(values=["No containers available"])
                self.container_var.set("No containers available")
                self.selected_container = None
                self.refresh_graphs()
                
            # Store container map for future reference
            self.container_map = container_map
            
        except Exception as e:
            logger.error(f"Error updating container selector: {e}")
            
    def on_container_selected(self, container_name):
        """
        Handle container selection change.
        
        Args:
            container_name: Selected container display name
        """
        try:
            # Get container ID from name
            if container_name in self.container_map:
                self.selected_container = self.container_map[container_name]
                self.refresh_graphs()
            else:
                self.selected_container = None
                
        except Exception as e:
            logger.error(f"Error selecting container: {e}")
            
    def refresh_graphs(self, *args):
        """Refresh graph visualizations."""
        try:
            if not self.selected_container:
                # Clear graphs
                self.cpu_chart_placeholder.pack(expand=True, fill="both", padx=15, pady=15)
                self.memory_chart_placeholder.pack(expand=True, fill="both", padx=15, pady=15)
                return
                
            # Show loading message
            self.cpu_chart_placeholder.configure(text="Loading CPU metrics...")
            self.memory_chart_placeholder.configure(text="Loading memory metrics...")
            
            # Get metrics in background thread
            threading.Thread(target=self.generate_graphs, daemon=True).start()
            
            # Update refresh time
            self.refresh_label.configure(text=f"Last updated: {time.strftime('%H:%M:%S')}")
            
        except Exception as e:
            logger.error(f"Error refreshing graphs: {e}")
            self.cpu_chart_placeholder.configure(text=f"Error loading metrics: {e}")
            self.memory_chart_placeholder.configure(text=f"Error loading metrics: {e}")
            
    def generate_graphs(self):
        """Generate graph visualizations in a background thread."""
        try:
            # Get metrics history for the selected container
            metrics_history = self.container_monitor.get_metrics_history(self.selected_container or "")
            
            if not metrics_history:
                self.after(0, lambda: self.cpu_chart_placeholder.configure(
                    text="No metrics data available for this container"))
                self.after(0, lambda: self.memory_chart_placeholder.configure(
                    text="No metrics data available for this container"))
                return
                
            # Filter metrics based on selected time range
            filtered_metrics = self.filter_metrics_by_time_range(metrics_history)
            
            if not filtered_metrics:
                self.after(0, lambda: self.cpu_chart_placeholder.configure(
                    text="No metrics data available for the selected time range"))
                self.after(0, lambda: self.memory_chart_placeholder.configure(
                    text="No metrics data available for the selected time range"))
                return
                
            # Extract data for plots
            timestamps = []
            cpu_values = []
            memory_values = []
            
            for metric in filtered_metrics:
                timestamps.append(datetime.datetime.fromtimestamp(metric.get('timestamp', 0)))
                cpu_values.append(metric.get('cpu_percent', 0))
                memory_values.append(metric.get('memory_percent', 0))
                
            # Create Plotly figure for CPU
            cpu_fig = go.Figure()
            cpu_fig.add_trace(go.Scatter(
                x=timestamps,
                y=cpu_values,
                mode='lines',
                name='CPU Usage',
                line=dict(color=SPOTIFY_COLORS["accent_green"], width=2),
                fill='tozeroy',
                fillcolor=f'rgba({int(SPOTIFY_COLORS["accent_green"][1:3], 16)}, '
                           f'{int(SPOTIFY_COLORS["accent_green"][3:5], 16)}, '
                           f'{int(SPOTIFY_COLORS["accent_green"][5:7], 16)}, 0.2)'
            ))
            
            cpu_fig.update_layout(
                plot_bgcolor='rgba(0, 0, 0, 0)',
                paper_bgcolor='rgba(0, 0, 0, 0)',
                margin=dict(l=20, r=20, t=10, b=30),
                xaxis=dict(
                    showgrid=True,
                    gridcolor='rgba(255, 255, 255, 0.1)',
                    tickfont=dict(color=SPOTIFY_COLORS["text_subtle"]),
                    title_font=dict(color=SPOTIFY_COLORS["text_subtle"]),
                    title_text="Time"
                ),
                yaxis=dict(
                    showgrid=True,
                    gridcolor='rgba(255, 255, 255, 0.1)',
                    tickfont=dict(color=SPOTIFY_COLORS["text_subtle"]),
                    title_font=dict(color=SPOTIFY_COLORS["text_subtle"]),
                    title_text="CPU Usage (%)",
                    range=[0, max(100, max(cpu_values) * 1.1) if cpu_values else 100]
                ),
                hovermode='x unified',
                font=dict(color=SPOTIFY_COLORS["text_bright"])
            )
            
            # Create Plotly figure for Memory
            memory_fig = go.Figure()
            memory_fig.add_trace(go.Scatter(
                x=timestamps,
                y=memory_values,
                mode='lines',
                name='Memory Usage',
                line=dict(color=SPOTIFY_COLORS["accent_purple"], width=2),
                fill='tozeroy',
                fillcolor=f'rgba({int(SPOTIFY_COLORS["accent_purple"][1:3], 16)}, '
                           f'{int(SPOTIFY_COLORS["accent_purple"][3:5], 16)}, '
                           f'{int(SPOTIFY_COLORS["accent_purple"][5:7], 16)}, 0.2)'
            ))
            
            memory_fig.update_layout(
                plot_bgcolor='rgba(0, 0, 0, 0)',
                paper_bgcolor='rgba(0, 0, 0, 0)',
                margin=dict(l=20, r=20, t=10, b=30),
                xaxis=dict(
                    showgrid=True,
                    gridcolor='rgba(255, 255, 255, 0.1)',
                    tickfont=dict(color=SPOTIFY_COLORS["text_subtle"]),
                    title_font=dict(color=SPOTIFY_COLORS["text_subtle"]),
                    title_text="Time"
                ),
                yaxis=dict(
                    showgrid=True,
                    gridcolor='rgba(255, 255, 255, 0.1)',
                    tickfont=dict(color=SPOTIFY_COLORS["text_subtle"]),
                    title_font=dict(color=SPOTIFY_COLORS["text_subtle"]),
                    title_text="Memory Usage (%)",
                    range=[0, max(100, max(memory_values) * 1.1) if memory_values else 100]
                ),
                hovermode='x unified',
                font=dict(color=SPOTIFY_COLORS["text_bright"])
            )
            
            # Convert to HTML
            cpu_html = cpu_fig.to_html(full_html=False, include_plotlyjs='cdn')
            memory_html = memory_fig.to_html(full_html=False, include_plotlyjs='cdn')
            
            # Store HTML
            self.cpu_plot_html = cpu_html
            self.memory_plot_html = memory_html
            
            # Update UI in main thread
            self.after(0, self.update_graph_ui)
            
        except Exception as e:
            logger.error(f"Error generating graphs: {e}")
            self.after(0, lambda: self.cpu_chart_placeholder.configure(
                text=f"Error generating CPU graph: {e}"))
            self.after(0, lambda: self.memory_chart_placeholder.configure(
                text=f"Error generating memory graph: {e}"))
            
    def update_graph_ui(self):
        """Update graph UI with generated HTML."""
        try:
            # Remove placeholder
            self.cpu_chart_placeholder.pack_forget()
            self.memory_chart_placeholder.pack_forget()
            
            # Create or update browser frames for graphs
            if not hasattr(self, 'cpu_html_frame'):
                # We need to use a different approach since browser widget is not available in CustomTkinter
                # For simplicity, we'll use a text widget with HTML rendering
                # In a production app, you'd integrate with something like PyWebView or another HTML renderer
                
                # For CPU graph
                self.cpu_html_frame = ctk.CTkFrame(
                    self.cpu_chart_frame,
                    fg_color=scale_color(SPOTIFY_COLORS["card_background"], 1.05),
                    corner_radius=5
                )
                self.cpu_html_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))
                
                self.cpu_text = ctk.CTkTextbox(
                    self.cpu_html_frame,
                    fg_color="transparent",
                    text_color=SPOTIFY_COLORS["text_bright"],
                    font=("Helvetica", 12)
                )
                self.cpu_text.pack(fill="both", expand=True, padx=5, pady=5)
                
                # For Memory graph
                self.memory_html_frame = ctk.CTkFrame(
                    self.memory_chart_frame,
                    fg_color=scale_color(SPOTIFY_COLORS["card_background"], 1.05),
                    corner_radius=5
                )
                self.memory_html_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))
                
                self.memory_text = ctk.CTkTextbox(
                    self.memory_html_frame,
                    fg_color="transparent",
                    text_color=SPOTIFY_COLORS["text_bright"],
                    font=("Helvetica", 12)
                )
                self.memory_text.pack(fill="both", expand=True, padx=5, pady=5)
            
            # Update text content with visualization placeholder
            # In a real app with HTML rendering:
            # self.cpu_browser.load_html(self.cpu_plot_html)
            # self.memory_browser.load_html(self.memory_plot_html)
            
            # Display ASCII art charts as a fallback visualization
            filtered_metrics = self.filter_metrics_by_time_range(
                self.container_monitor.get_metrics_history(self.selected_container or "") or []
            )
            
            # CPU visualization
            self.cpu_text.configure(state="normal")
            self.cpu_text.delete("1.0", "end")
            
            if filtered_metrics:
                # Extract CPU data
                timestamps = [datetime.datetime.fromtimestamp(m.get('timestamp', 0)) for m in filtered_metrics]
                cpu_values = [m.get('cpu_percent', 0) for m in filtered_metrics]
                
                # Create ASCII chart for CPU
                chart_width = 50
                chart_height = 6  # Reduced height to make chart more compact
                
                # Scale values to chart height
                max_cpu = max(cpu_values) if cpu_values else 100
                if max_cpu < 5:  # If very small values, set a minimum for better visibility
                    max_cpu = 5
                
                # Create chart header
                time_range = self.time_range_var.get()
                cpu_chart = f"CPU Usage Chart ({time_range})\n"
                cpu_chart += f"Container: {self.selected_container[:12] if self.selected_container else 'None'}\n"
                cpu_chart += f"Max: {max_cpu:.1f}%\n"
                cpu_chart += f"Current: {cpu_values[-1] if cpu_values else 0:.1f}%\n\n"
                
                # Create chart
                for y in range(chart_height, 0, -1):
                    threshold = max_cpu * y / chart_height
                    cpu_chart += f"{threshold:5.1f}% |"
                    
                    for x in range(min(len(cpu_values), chart_width)):
                        idx = len(cpu_values) - chart_width + x if len(cpu_values) > chart_width else x
                        if cpu_values[idx] >= threshold:
                            cpu_chart += "█"
                        else:
                            cpu_chart += " "
                    
                    cpu_chart += "|\n"
                
                # Create chart footer
                cpu_chart += "       "
                cpu_chart += "-" * (min(len(cpu_values), chart_width) + 2) + "\n"
                
                # Time scale
                if len(timestamps) > 1:
                    first_time = timestamps[0] if len(timestamps) <= chart_width else timestamps[-chart_width]
                    last_time = timestamps[-1]
                    
                    cpu_chart += f"       {first_time.strftime('%H:%M:%S')}".ljust(chart_width//2 + 8)
                    cpu_chart += f"{last_time.strftime('%H:%M:%S')}\n"
                
                # Add data points count
                cpu_chart += f"\nData points: {len(filtered_metrics)}"
                
                self.cpu_text.insert("1.0", cpu_chart)
            else:
                self.cpu_text.insert("1.0", "No CPU metrics data available for the selected time range.")
                
            self.cpu_text.configure(state="disabled")
            
            # Memory visualization
            self.memory_text.configure(state="normal")
            self.memory_text.delete("1.0", "end")
            
            if filtered_metrics:
                # Extract memory data
                timestamps = [datetime.datetime.fromtimestamp(m.get('timestamp', 0)) for m in filtered_metrics]
                memory_values = [m.get('memory_percent', 0) for m in filtered_metrics]
                memory_usage = [m.get('memory_usage', 0) / (1024*1024) for m in filtered_metrics]  # MB
                
                # Create ASCII chart for memory
                chart_width = 50
                chart_height = 6  # Reduced height to make chart more compact
                
                # Scale values to chart height
                max_memory = max(memory_values) if memory_values else 100
                if max_memory < 5:  # If very small values, set a minimum for better visibility
                    max_memory = 5
                
                # Get current memory usage in MB
                current_memory_mb = memory_usage[-1] if memory_usage else 0
                
                # Create chart header
                time_range = self.time_range_var.get()
                memory_chart = f"Memory Usage Chart ({time_range})\n"
                memory_chart += f"Container: {self.selected_container[:12] if self.selected_container else 'None'}\n"
                memory_chart += f"Max: {max_memory:.1f}%\n"
                memory_chart += f"Current: {memory_values[-1] if memory_values else 0:.1f}% ({current_memory_mb:.1f} MB)\n\n"
                
                # Create chart
                for y in range(chart_height, 0, -1):
                    threshold = max_memory * y / chart_height
                    memory_chart += f"{threshold:5.1f}% |"
                    
                    for x in range(min(len(memory_values), chart_width)):
                        idx = len(memory_values) - chart_width + x if len(memory_values) > chart_width else x
                        if memory_values[idx] >= threshold:
                            memory_chart += "█"
                        else:
                            memory_chart += " "
                    
                    memory_chart += "|\n"
                
                # Create chart footer
                memory_chart += "       "
                memory_chart += "-" * (min(len(memory_values), chart_width) + 2) + "\n"
                
                # Time scale
                if len(timestamps) > 1:
                    first_time = timestamps[0] if len(timestamps) <= chart_width else timestamps[-chart_width]
                    last_time = timestamps[-1]
                    
                    memory_chart += f"       {first_time.strftime('%H:%M:%S')}".ljust(chart_width//2 + 8)
                    memory_chart += f"{last_time.strftime('%H:%M:%S')}\n"
                
                # Add data points count
                memory_chart += f"\nData points: {len(filtered_metrics)}"
                
                self.memory_text.insert("1.0", memory_chart)
            else:
                self.memory_text.insert("1.0", "No memory metrics data available for the selected time range.")
                
            self.memory_text.configure(state="disabled")
            
        except Exception as e:
            logger.error(f"Error updating graph UI: {e}")
            self.cpu_chart_placeholder.configure(text=f"Error displaying CPU graph: {e}")
            self.cpu_chart_placeholder.pack(expand=True, fill="both", padx=15, pady=15)
            
            self.memory_chart_placeholder.configure(text=f"Error displaying memory graph: {e}")
            self.memory_chart_placeholder.pack(expand=True, fill="both", padx=15, pady=15)
            
    def filter_metrics_by_time_range(self, metrics: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter metrics based on selected time range.
        
        Args:
            metrics: List of metrics dictionaries
            
        Returns:
            Filtered metrics list
        """
        if not metrics:
            return []
            
        # Get current time
        now = time.time()
        
        # Determine time range in seconds
        time_range = self.time_range_var.get()
        if time_range == "Last 5 minutes":
            range_seconds = 5 * 60
        elif time_range == "Last 15 minutes":
            range_seconds = 15 * 60
        elif time_range == "Last hour":
            range_seconds = 60 * 60
        else:  # All
            return metrics
            
        # Filter metrics
        return [m for m in metrics if now - m.get('timestamp', 0) <= range_seconds]
        
    def update_metrics(self, metrics: Dict[str, Dict[str, Any]]):
        """
        Update metrics data.
        
        Args:
            metrics: Dictionary of container metrics
        """
        # Store current metrics
        self.current_metrics = metrics
        
        # Refresh graphs if needed
        if self.selected_container and self.selected_container in metrics:
            # Only refresh if graphs are visible
            if self.winfo_ismapped() and self.selected_container:
                self.refresh_graphs()
