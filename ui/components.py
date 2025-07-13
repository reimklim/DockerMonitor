"""
UI components for Dockify.
This module provides reusable UI components for the Dockify application.
"""
import logging
import math
import time
import tkinter as tk
from tkinter import ttk
from typing import Dict, List, Any, Optional, Callable, Tuple, Union
from datetime import datetime, timedelta
import calendar
import threading

import customtkinter as ctk

from utils.theme import SPOTIFY_COLORS, lighten_color, scale_color
from assets.icons import get_icon_image
from utils.compat import get_compatible_color

logger = logging.getLogger('dockify.ui.components')

class GradientFrame(ctk.CTkFrame):
    """
    Frame with a vertical gradient background.
    """
    def __init__(self, parent, start_color: str, end_color: str, height: int = 100, **kwargs):
        """
        Initialize gradient frame.
        
        Args:
            parent: Parent widget
            start_color: Starting gradient color (hex)
            end_color: Ending gradient color (hex)
            height: Frame height
            **kwargs: Additional arguments for CTkFrame
        """
        super().__init__(
            parent,
            height=height,
            fg_color="transparent",
            **kwargs
        )
        
        self.start_color = start_color
        self.end_color = end_color
        self.bind("<Configure>", self._draw_gradient)
        
    def _draw_gradient(self, event=None):
        """Draw the gradient background."""
        width = self.winfo_width()
        height = self.winfo_height()
        
        if width <= 1 or height <= 1:
            return
        
        # Create a new canvas if needed
        if not hasattr(self, 'canvas') or not self.canvas.winfo_exists():
            self.canvas = tk.Canvas(
                self,
                width=width,
                height=height,
                highlightthickness=0
            )
            self.canvas.place(x=0, y=0, relwidth=1, relheight=1)
        
        self.canvas.delete("gradient")
        
        # Parse colors
        r1, g1, b1 = int(self.start_color[1:3], 16), int(self.start_color[3:5], 16), int(self.start_color[5:7], 16)
        r2, g2, b2 = int(self.end_color[1:3], 16), int(self.end_color[3:5], 16), int(self.end_color[5:7], 16)
        
        # Draw gradient lines
        for i in range(height):
            # Linear interpolation
            r = r1 + (r2 - r1) * i / height
            g = g1 + (g2 - g1) * i / height
            b = b1 + (b2 - b1) * i / height
            
            color = f'#{int(r):02x}{int(g):02x}{int(b):02x}'
            self.canvas.create_line(0, i, width, i, fill=color, tags="gradient")
            
        # Bring all child widgets to the front
        for child in self.winfo_children():
            if child is not self.canvas:
                self.canvas.tag_lower("gradient")


class CardFrame(ctk.CTkFrame):
    """
    Card-like frame with rounded corners and optional hover effects.
    """
    def __init__(self, parent, hoverable: bool = False, **kwargs):
        """
        Initialize card frame.
        
        Args:
            parent: Parent widget
            hoverable: Whether to show hover effects
            **kwargs: Additional arguments for CTkFrame
        """
        kwargs.setdefault("fg_color", SPOTIFY_COLORS["card_background"])
        kwargs.setdefault("corner_radius", 10)
        kwargs.setdefault("border_width", 0)
        
        super().__init__(
            parent,
            **kwargs
        )
        
        self.hoverable = hoverable
        self.normal_color = kwargs.get("fg_color", SPOTIFY_COLORS["card_background"])
        self.hover_color = lighten_color(self.normal_color, 0.1)
        
        if hoverable:
            self.bind("<Enter>", self._on_enter)
            self.bind("<Leave>", self._on_leave)
    
    def _on_enter(self, event):
        """Handle mouse enter event."""
        if self.hoverable:
            self.configure(fg_color=self.hover_color)
    
    def _on_leave(self, event):
        """Handle mouse leave event."""
        if self.hoverable:
            self.configure(fg_color=self.normal_color)


class CircularProgressBar(ctk.CTkFrame):
    """
    Circular progress bar widget with Spotify-inspired styling.
    """
    def __init__(self, parent, size: int = 100, progress: float = 0.0, 
                 fg_color: str = SPOTIFY_COLORS["accent"], 
                 text: str = "", **kwargs):
        """
        Initialize circular progress bar.
        
        Args:
            parent: Parent widget
            size: Size of widget in pixels
            progress: Initial progress value (0.0 to 1.0)
            fg_color: Progress bar color
            text: Text to display in center
            **kwargs: Additional arguments for CTkFrame
        """
        super().__init__(
            parent,
            width=size,
            height=size,
            fg_color="transparent",
            **kwargs
        )
        
        self.size = size
        self.progress = min(max(progress, 0.0), 1.0)
        self.fg_color = fg_color
        self.text = text
        
        # Create canvas for drawing
        self.canvas = tk.Canvas(
            self,
            width=size,
            height=size,
            bg=SPOTIFY_COLORS["background"],
            highlightthickness=0
        )
        self.canvas.place(relx=0.5, rely=0.5, anchor="center")
        
        # Create text label
        self.label = ctk.CTkLabel(
            self,
            text=text,
            font=("Helvetica", int(size / 5)),
            text_color=SPOTIFY_COLORS["text_bright"]
        )
        self.label.place(relx=0.5, rely=0.5, anchor="center")
        
        # Draw initial state
        self.draw()
        
    def draw(self):
        """Draw the progress bar."""
        self.canvas.delete("progress")
        
        # Constants
        center_x = self.size / 2
        center_y = self.size / 2
        radius = (self.size / 2) * 0.8
        thickness = self.size * 0.1
        
        # Background circle
        self.canvas.create_oval(
            center_x - radius,
            center_y - radius,
            center_x + radius,
            center_y + radius,
            outline=scale_color(SPOTIFY_COLORS["card_background"], 1.1),
            width=thickness,
            tags="progress"
        )
        
        if self.progress > 0:
            # Calculate start and end angles
            start_angle = 90  # Start from top
            extent = -self.progress * 360  # Negative for clockwise
            
            # Progress arc
            self.canvas.create_arc(
                center_x - radius,
                center_y - radius,
                center_x + radius,
                center_y + radius,
                start=start_angle,
                extent=extent,
                outline=self.fg_color,
                width=thickness,
                style=tk.ARC,
                tags="progress"
            )
    
    def set_progress(self, progress: float):
        """
        Set progress value.
        
        Args:
            progress: Progress value (0.0 to 1.0)
        """
        self.progress = min(max(progress, 0.0), 1.0)
        self.draw()
    
    def set_text(self, text: str):
        """
        Set label text.
        
        Args:
            text: Text to display
        """
        self.text = text
        self.label.configure(text=text)


class SpotifyButton(ctk.CTkButton):
    """
    Button with Spotify-inspired styling.
    """
    def __init__(self, parent, text: str = "", 
                 button_type: str = "primary",
                 icon_name: Optional[str] = None, **kwargs):
        """
        Initialize Spotify-style button.
        
        Args:
            parent: Parent widget
            text: Button text
            button_type: Button type ('primary', 'secondary', 'text', or 'danger')
            icon_name: Name of icon to display
            **kwargs: Additional arguments for CTkButton
        """
        # Configure colors based on button type
        if button_type == "primary":
            fg_color = SPOTIFY_COLORS["accent"]
            hover_color = lighten_color(SPOTIFY_COLORS["accent"], 0.1)
            text_color = SPOTIFY_COLORS["text_bright"]
        elif button_type == "secondary":
            fg_color = scale_color(SPOTIFY_COLORS["card_background"], 1.1)
            hover_color = scale_color(SPOTIFY_COLORS["card_background"], 1.2)
            text_color = SPOTIFY_COLORS["text_standard"]
        elif button_type == "text":
            fg_color = "transparent"
            hover_color = scale_color(SPOTIFY_COLORS["card_background"], 1.1)
            text_color = SPOTIFY_COLORS["text_standard"]
        elif button_type == "danger":
            fg_color = SPOTIFY_COLORS["accent_red"]
            hover_color = lighten_color(SPOTIFY_COLORS["accent_red"], 0.1)
            text_color = SPOTIFY_COLORS["text_bright"]
        else:
            fg_color = kwargs.get("fg_color", SPOTIFY_COLORS["accent"])
            hover_color = kwargs.get("hover_color", lighten_color(fg_color, 0.1))
            text_color = kwargs.get("text_color", SPOTIFY_COLORS["text_bright"])
        
        # Override with kwargs if provided
        kwargs.setdefault("fg_color", fg_color)
        kwargs.setdefault("hover_color", hover_color)
        kwargs.setdefault("text_color", text_color)
        kwargs.setdefault("corner_radius", 5)
        
        # Create image if icon is provided
        image = None
        if icon_name:
            try:
                image = get_icon_image(
                    icon_name, 
                    size=20, 
                    color=kwargs.get("text_color", text_color)
                )
                # Если изображение не удалось создать, просто продолжаем без него
                if image is None:
                    logger.warning(f"Failed to create image for SpotifyButton: {icon_name}")
            except Exception as e:
                # Логируем ошибку и продолжаем без изображения
                logger.warning(f"Error creating image for SpotifyButton: {e}")
        
        # Initialize button with or without image
        if image:
            super().__init__(
                parent,
                text=text,
                image=image,
                compound="left",
                **kwargs
            )
        else:
            super().__init__(
                parent,
                text=text,
                **kwargs
            )


class AlertNotification(ctk.CTkFrame):
    """
    Notification widget for displaying alerts.
    """
    def __init__(self, parent, alert: Dict[str, Any], **kwargs):
        """
        Initialize alert notification.
        
        Args:
            parent: Parent widget
            alert: Alert dictionary
            **kwargs: Additional arguments for CTkFrame
        """
        super().__init__(
            parent,
            fg_color=scale_color(SPOTIFY_COLORS["card_background"], 1.1),
            corner_radius=5,
            border_width=1,
            border_color=SPOTIFY_COLORS["accent_red"],
            **kwargs
        )
        
        self.alert = alert
        self.opacity = 1.0
        
        # Determine severity colors
        severity = alert.get("severity", "warning")
        if severity == "critical":
            border_color = SPOTIFY_COLORS["accent_red"]
            icon_name = "alert_critical"
        elif severity == "warning":
            border_color = SPOTIFY_COLORS["accent_orange"]
            icon_name = "alert_warning"
        else:
            border_color = SPOTIFY_COLORS["accent_blue"]
            icon_name = "alert_info"
            
        self.configure(border_color=border_color)
        
        # Create inner padding frame
        self.inner_frame = ctk.CTkFrame(
            self,
            fg_color="transparent"
        )
        self.inner_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create header with container name and timestamp
        self.header_frame = ctk.CTkFrame(
            self.inner_frame,
            fg_color="transparent"
        )
        self.header_frame.pack(fill="x", pady=(0, 5))
        
        # Alert icon
        try:
            self.icon = get_icon_image(icon_name, size=16, color=border_color)
            self.icon_label = ctk.CTkLabel(
                self.header_frame,
                text="",
                image=self.icon,
                fg_color="transparent"
            )
        except Exception as e:
            logger.warning(f"Failed to create alert icon: {e}")
            # Используем текстовый символ вместо иконки
            self.icon_label = ctk.CTkLabel(
                self.header_frame,
                text="⚠",  # Unicode warning symbol as fallback
                font=("Helvetica", 14),
                text_color=border_color,
                fg_color="transparent"
            )
        self.icon_label.pack(side="left", padx=(0, 5))
        
        # Container name
        self.container_label = ctk.CTkLabel(
            self.header_frame,
            text=alert.get("container_name", "Unknown container"),
            font=("Helvetica", 12, "bold"),
            text_color=SPOTIFY_COLORS["text_bright"],
            fg_color="transparent"
        )
        self.container_label.pack(side="left", fill="x", expand=True)
        
        # Timestamp
        self.timestamp_label = ctk.CTkLabel(
            self.header_frame,
            text=alert.get("timestamp", ""),
            font=("Helvetica", 10),
            text_color=SPOTIFY_COLORS["text_subtle"],
            fg_color="transparent"
        )
        self.timestamp_label.pack(side="right")
        
        # Message
        self.message_label = ctk.CTkLabel(
            self.inner_frame,
            text=alert.get("message", ""),
            font=("Helvetica", 11),
            text_color=SPOTIFY_COLORS["text_standard"],
            fg_color="transparent",
            justify="left",
            wraplength=300
        )
        self.message_label.pack(fill="x", anchor="w")
        
        # Details/value
        if "value" in alert:
            self.value_label = ctk.CTkLabel(
                self.inner_frame,
                text=f"Value: {alert.get('value', 0):.1f}% (Threshold: {alert.get('threshold', 0):.1f}%)",
                font=("Helvetica", 10),
                text_color=SPOTIFY_COLORS["text_subtle"],
                fg_color="transparent"
            )
            self.value_label.pack(fill="x", anchor="w", pady=(5, 0))
        
        # Close button
        try:
            close_icon = get_icon_image("close", size=10, color=SPOTIFY_COLORS["text_subtle"])
            self.close_btn = ctk.CTkButton(
                self.inner_frame,
                text="",
                width=20,
                height=20,
                fg_color="transparent",
                hover_color=scale_color(SPOTIFY_COLORS["card_background"], 1.2),
                corner_radius=10,
                image=close_icon,
                command=self.destroy
            )
        except Exception as e:
            logger.warning(f"Failed to create close icon: {e}")
            self.close_btn = ctk.CTkButton(
                self.inner_frame,
                text="✕",  # Unicode X symbol as fallback
                width=20,
                height=20,
                fg_color="transparent",
                hover_color=scale_color(SPOTIFY_COLORS["card_background"], 1.2),
                corner_radius=10,
                command=self.destroy
            )
        self.close_btn.place(relx=1.0, rely=0.0, anchor="ne")
        
    def fade_out(self, duration: float = 0.5, callback: Optional[Callable] = None):
        """
        Fade out the notification.
        
        Args:
            duration: Fade duration in seconds
            callback: Function to call when fade is complete
        """
        # Number of steps
        steps = 20
        step_time = duration / steps
        step_opacity = 1.0 / steps
        
        def fade_step(step):
            if step >= steps or not self.winfo_exists():
                if callback and self.winfo_exists():
                    callback()
                return
            
            self.opacity -= step_opacity
            self._set_opacity(self.opacity)
            
            # Schedule next step
            self.after(int(step_time * 1000), lambda: fade_step(step + 1))
        
        # Start fade animation
        fade_step(0)
    
    def _set_opacity(self, opacity: float):
        """
        Set widget opacity.
        
        Args:
            opacity: Opacity value (0.0 to 1.0)
        """
        opacity = min(max(opacity, 0.0), 1.0)
        self.opacity = opacity
        
        # Apply opacity to background color
        bg_color = scale_color(SPOTIFY_COLORS["card_background"], 1.1, opacity)
        self.configure(fg_color=bg_color)
        
        # Apply opacity to text colors
        if hasattr(self, 'container_label'):
            text_color = scale_color(SPOTIFY_COLORS["text_bright"], 1.0, opacity)
            self.container_label.configure(text_color=text_color)
        
        if hasattr(self, 'message_label'):
            text_color = scale_color(SPOTIFY_COLORS["text_standard"], 1.0, opacity)
            self.message_label.configure(text_color=text_color)
        
        if hasattr(self, 'timestamp_label'):
            text_color = scale_color(SPOTIFY_COLORS["text_subtle"], 1.0, opacity)
            self.timestamp_label.configure(text_color=text_color)
            
        if hasattr(self, 'value_label'):
            text_color = scale_color(SPOTIFY_COLORS["text_subtle"], 1.0, opacity)
            self.value_label.configure(text_color=text_color)


class MetricCard(ctk.CTkFrame):
    """
    Card displaying a metric with icon, title, and value.
    """
    def __init__(self, parent, title: str, value: str = "", subtitle: str = "", 
                 icon: Optional[str] = None, progress: float = 0.0, 
                 color: str = SPOTIFY_COLORS["accent"], **kwargs):
        """
        Initialize metric card.
        
        Args:
            parent: Parent widget
            title: Card title
            value: Metric value
            subtitle: Subtitle or description
            icon: Icon name
            progress: Progress value (0.0 to 1.0)
            color: Accent color
            **kwargs: Additional arguments for CTkFrame
        """
        kwargs.setdefault("fg_color", SPOTIFY_COLORS["card_background"])
        kwargs.setdefault("corner_radius", 10)
        kwargs.setdefault("width", 175)
        kwargs.setdefault("height", 175)
        
        super().__init__(
            parent,
            **kwargs
        )
        
        # Store parameters
        self.title = title
        self.value = value
        self.subtitle = subtitle
        self.icon_name = icon
        self.progress = progress
        self.color = color
        
        # Create UI
        self.create_ui()
        
    def create_ui(self):
        """Create and setup the user interface."""
        # Make sure the frame has a minimum size
        self.pack_propagate(False)
        
        # Header with icon and title
        self.header_frame = ctk.CTkFrame(
            self,
            fg_color="transparent",
            height=40
        )
        self.header_frame.pack(fill="x", padx=15, pady=(15, 5))
        
        # Icon (if provided)
        if self.icon_name:
            try:
                self.icon = get_icon_image(self.icon_name, size=20, color=self.color)
                if self.icon:  # Проверяем, что иконка успешно создана
                    self.icon_label = ctk.CTkLabel(
                        self.header_frame,
                        text="",
                        image=self.icon
                    )
                    self.icon_label.pack(side="left", padx=(0, 5))
                else:
                    # Если иконка не создана, используем текстовую метку
                    self.icon_label = ctk.CTkLabel(
                        self.header_frame,
                        text="●",
                        font=("Helvetica", 16),
                        text_color=self.color
                    )
                    self.icon_label.pack(side="left", padx=(0, 5))
            except Exception as e:
                # В случае ошибки используем текстовую метку
                logger.warning(f"Failed to create icon for MetricCard: {e}")
                self.icon_label = ctk.CTkLabel(
                    self.header_frame,
                    text="●",
                    font=("Helvetica", 16),
                    text_color=self.color
                )
                self.icon_label.pack(side="left", padx=(0, 5))
        
        # Title
        self.title_label = ctk.CTkLabel(
            self.header_frame,
            text=self.title,
            font=("Helvetica", 12, "bold"),
            text_color=SPOTIFY_COLORS["text_standard"]
        )
        self.title_label.pack(side="left", fill="x", expand=True)
        
        # Value
        self.value_label = ctk.CTkLabel(
            self,
            text=self.value,
            font=("Helvetica", 24, "bold"),
            text_color=SPOTIFY_COLORS["text_bright"]
        )
        self.value_label.pack(pady=(10, 0))
        
        # Subtitle (if provided)
        if self.subtitle:
            self.subtitle_label = ctk.CTkLabel(
                self,
                text=self.subtitle,
                font=("Helvetica", 12),
                text_color=SPOTIFY_COLORS["text_subtle"]
            )
            self.subtitle_label.pack(pady=(0, 10))
        
        # Progress indicator
        self.progress_frame = ctk.CTkFrame(
            self,
            fg_color="transparent",
            height=30
        )
        self.progress_frame.pack(fill="x", side="bottom", padx=15, pady=15)
        
        self.progress_bar = ctk.CTkProgressBar(
            self.progress_frame,
            width=self.winfo_width() - 30,
            height=5,
            progress_color=self.color,
            corner_radius=2
        )
        self.progress_bar.pack(fill="x")
        self.progress_bar.set(self.progress)
    
    def update_values(self, value: str, subtitle: Optional[str] = None, progress: Optional[float] = None):
        """
        Update card values.
        
        Args:
            value: New value
            subtitle: New subtitle (optional)
            progress: New progress value (optional)
        """
        # Update value
        self.value = value
        self.value_label.configure(text=value)
        
        # Update subtitle if provided
        if subtitle is not None and hasattr(self, 'subtitle_label'):
            self.subtitle = subtitle
            self.subtitle_label.configure(text=subtitle)
        
        # Update progress if provided
        if progress is not None:
            self.progress = min(max(progress, 0.0), 1.0)
            self.progress_bar.set(self.progress)


class StatusIndicator(ctk.CTkFrame):
    """
    Status indicator widget showing a colored indicator dot.
    """
    def __init__(self, parent, status: str = "gray", size: int = 10, **kwargs):
        """
        Initialize status indicator.
        
        Args:
            parent: Parent widget
            status: Status color ('green', 'yellow', 'red', or 'gray')
            size: Size of indicator
            **kwargs: Additional arguments for CTkFrame
        """
        kwargs.setdefault("fg_color", "transparent")
        kwargs.setdefault("width", size)
        kwargs.setdefault("height", size)
        
        super().__init__(
            parent,
            **kwargs
        )
        
        # Status colors
        self.colors = {
            "green": SPOTIFY_COLORS["accent_green"],
            "yellow": SPOTIFY_COLORS["accent_yellow"],
            "red": SPOTIFY_COLORS["accent_red"],
            "gray": SPOTIFY_COLORS["text_subtle"]
        }
        
        self.size = size
        self.status = status
        
        # Получаем цвет фона родительского элемента, чтобы холст был незаметен
        parent_bg = parent.cget("fg_color") if hasattr(parent, "cget") else None
        if parent_bg == "transparent" or parent_bg is None:
            # Если родительский элемент прозрачный, используем цвет фона карточки
            canvas_bg = scale_color(SPOTIFY_COLORS["card_background"], 1.1)
        else:
            # Иначе используем цвет родительского элемента
            canvas_bg = parent_bg
        
        # Create the indicator canvas
        self.canvas = tk.Canvas(
            self,
            width=size,
            height=size,
            bg=canvas_bg,
            highlightthickness=0
        )
        self.canvas.pack(fill="both", expand=True)
        
        # Draw the indicator
        self.draw()
    
    def draw(self):
        """Draw the indicator dot."""
        self.canvas.delete("indicator")
        
        # Get color for current status
        color = self.colors.get(self.status, self.colors["gray"])
        
        # Draw the dot
        self.canvas.create_oval(
            1, 1, self.size - 1, self.size - 1,
            fill=color,
            outline=lighten_color(color, 0.1),
            tags="indicator"
        )
    
    def set_status(self, status: str):
        """
        Set the indicator status.
        
        Args:
            status: Status color ('green', 'yellow', 'red', or 'gray')
        """
        if status in self.colors:
            self.status = status
            self.draw()
            # Обновляем виджет, чтобы убедиться, что изменения отображаются
            self.update_idletasks()


class ActionButton(ctk.CTkButton):
    """
    Action button with icon and consistent styling.
    """
    def __init__(self, parent, text: str = "", icon_name: Optional[str] = None,
                 button_type: str = "primary", size: str = "medium", 
                 command: Optional[Callable] = None, **kwargs):
        """
        Initialize action button.
        
        Args:
            parent: Parent widget
            text: Button text
            icon_name: Icon name to display
            button_type: Button type ('primary', 'secondary', 'text', 'danger')
            size: Button size ('small', 'medium', 'large')
            command: Button command
            **kwargs: Additional arguments for CTkButton
        """
        # Configure colors based on button type
        if button_type == "primary":
            fg_color = SPOTIFY_COLORS["accent"]
            hover_color = lighten_color(SPOTIFY_COLORS["accent"], 0.1)
            text_color = SPOTIFY_COLORS["text_bright"]
        elif button_type == "secondary":
            fg_color = scale_color(SPOTIFY_COLORS["card_background"], 1.1)
            hover_color = scale_color(SPOTIFY_COLORS["card_background"], 1.2)
            text_color = SPOTIFY_COLORS["text_standard"]
        elif button_type == "text":
            fg_color = "transparent"
            hover_color = scale_color(SPOTIFY_COLORS["card_background"], 1.1)
            text_color = SPOTIFY_COLORS["text_standard"]
        elif button_type == "danger":
            fg_color = SPOTIFY_COLORS["accent_red"]
            hover_color = lighten_color(SPOTIFY_COLORS["accent_red"], 0.1)
            text_color = SPOTIFY_COLORS["text_bright"]
        else:
            fg_color = kwargs.get("fg_color", SPOTIFY_COLORS["accent"])
            hover_color = kwargs.get("hover_color", lighten_color(fg_color, 0.1))
            text_color = kwargs.get("text_color", SPOTIFY_COLORS["text_bright"])
            
        # Configure size
        if size == "small":
            height = 30
            font_size = 11
            icon_size = 16
            corner_radius = 4
        elif size == "large":
            height = 48
            font_size = 14
            icon_size = 24
            corner_radius = 8
        else:  # medium
            height = 38
            font_size = 12
            icon_size = 20
            corner_radius = 6
        
        # Create icon if provided
        image = None
        if icon_name:
            try:
                image = get_icon_image(
                    icon_name, 
                    size=icon_size, 
                    color=kwargs.get("text_color", text_color)
                )
                # Если изображение не удалось создать, просто продолжаем без него
                if image is None:
                    logger.warning(f"Failed to create image for ActionButton: {icon_name}")
            except Exception as e:
                # Логируем ошибку и продолжаем без изображения
                logger.warning(f"Error creating image for ActionButton: {e}")
        
        # Override with kwargs if provided
        kwargs.setdefault("fg_color", fg_color)
        kwargs.setdefault("hover_color", hover_color)
        kwargs.setdefault("text_color", text_color)
        kwargs.setdefault("corner_radius", corner_radius)
        kwargs.setdefault("height", height)
        kwargs.setdefault("font", ("Helvetica", font_size))
        
        # Инициализируем кнопку только с изображением, если оно успешно создано
        if image:
            super().__init__(
                parent,
                text=text,
                image=image,
                compound="left",
                command=command,
                **kwargs
            )
        else:
            # Без изображения
            super().__init__(
                parent,
                text=text,
                command=command,
                **kwargs
            )


class DropdownSelector(ctk.CTkFrame):
    """
    Custom dropdown selector with label and styled dropdown.
    """
    def __init__(self, parent, label: str = "", values: List[str] = [], 
                 default_value: str = "", width: int = 200,
                 command: Optional[Callable[[str], None]] = None,
                 variable: Optional[tk.StringVar] = None, **kwargs):
        """
        Initialize dropdown selector.
        
        Args:
            parent: Parent widget
            label: Label text
            values: List of values for dropdown
            default_value: Default value to select
            width: Width of widget
            command: Callback function for value change
            variable: StringVar for tracking value
            **kwargs: Additional arguments for CTkFrame
        """
        # Extract variable from kwargs to avoid passing to CTkFrame
        if 'variable' in kwargs:
            variable = kwargs.pop('variable')
            
        kwargs.setdefault("fg_color", get_compatible_color("transparent"))
        kwargs.setdefault("height", 64)
        
        super().__init__(
            parent,
            width=width,
            **kwargs
        )
        
        # Store properties
        self.values = values or []
        self.command = command
        self.variable = variable
        
        # Create UI
        self.label = ctk.CTkLabel(
            self,
            text=label,
            font=("Helvetica", 12),
            text_color=SPOTIFY_COLORS["text_standard"],
            anchor="w"
        )
        self.label.pack(fill="x", padx=5, pady=(5, 2))
        
        # Dropdown
        self.combobox = ctk.CTkComboBox(
            self,
            values=self.values,
            width=width-10,
            height=30,
            border_width=1,
            border_color=scale_color(SPOTIFY_COLORS["card_background"], 1.2),
            button_color=SPOTIFY_COLORS["accent"],
            button_hover_color=lighten_color(SPOTIFY_COLORS["accent"], 0.1),
            dropdown_fg_color=scale_color(SPOTIFY_COLORS["card_background"], 1.1),
            dropdown_hover_color=scale_color(SPOTIFY_COLORS["card_background"], 1.2),
            dropdown_text_color=SPOTIFY_COLORS["text_standard"],
            text_color=SPOTIFY_COLORS["text_bright"],
            fg_color=scale_color(SPOTIFY_COLORS["card_background"], 1.1),
            command=self._on_value_change
        )
        self.combobox.pack(fill="x", padx=5, pady=(0, 5))
        
        # Set initial value
        if self.variable:
            self.combobox.set(self.variable.get())
        elif default_value and default_value in self.values:
            self.combobox.set(default_value)
        elif self.values:
            self.combobox.set(self.values[0])
    
    def get(self) -> str:
        """
        Get current value.
        
        Returns:
            Current selected value
        """
        return self.combobox.get()
    
    def set(self, value: str) -> None:
        """
        Set current value.
        
        Args:
            value: Value to set
        """
        if value in self.values:
            self.combobox.set(value)
    
    def configure(self, **kwargs):
        """
        Configure dropdown.
        
        Args:
            **kwargs: Configuration options
        """
        # Handle 'values' parameter specially
        if 'values' in kwargs:
            values = kwargs.pop('values')
            self.configure_values(values)
            
        # Forward remaining options to the combobox
        if kwargs:
            self.combobox.configure(**kwargs)
            
    def configure_values(self, values: List[str], default_value: str = "") -> None:
        """
        Configure dropdown values.
        
        Args:
            values: New values for dropdown
            default_value: Default value to select
        """
        self.values = values
        self.combobox.configure(values=values)
        
        if default_value and default_value in self.values:
            self.combobox.set(default_value)
        elif self.values:
            self.combobox.set(self.values[0])
    
    def _on_value_change(self, value: str) -> None:
        """
        Handle value change.
        
        Args:
            value: New value
        """
        # Update StringVar if it exists
        if hasattr(self, 'variable') and self.variable:
            self.variable.set(value)
            
        # Call command callback if exists
        if self.command:
            self.command(value)


class DateSelector(ctk.CTkFrame):
    """
    Date selector widget with label and date entry.
    """
    def __init__(self, parent, label: str = "", default_date: Optional[str] = None, 
                 width: int = 200, command: Optional[Callable[[str], None]] = None, **kwargs):
        """
        Initialize date selector.
        
        Args:
            parent: Parent widget
            label: Label text
            default_date: Default date (YYYY-MM-DD format)
            width: Width of widget
            command: Callback function for date change
            **kwargs: Additional arguments for CTkFrame
        """
        kwargs.setdefault("fg_color", "transparent")
        kwargs.setdefault("height", 64)
        
        super().__init__(
            parent,
            width=width,
            **kwargs
        )
        
        # Store properties
        self.command = command
        self.date_format = "%Y-%m-%d"
        
        # Create UI
        self.label = ctk.CTkLabel(
            self,
            text=label,
            font=("Helvetica", 12),
            text_color=SPOTIFY_COLORS["text_standard"],
            anchor="w"
        )
        self.label.pack(fill="x", padx=5, pady=(5, 2))
        
        # Date entry frame
        self.entry_frame = ctk.CTkFrame(
            self,
            fg_color=scale_color(SPOTIFY_COLORS["card_background"], 1.1),
            corner_radius=5,
            border_width=1,
            border_color=scale_color(SPOTIFY_COLORS["card_background"], 1.2),
            height=30
        )
        self.entry_frame.pack(fill="x", padx=5, pady=(0, 5))
        
        # Make sure the entry frame doesn't resize
        self.entry_frame.pack_propagate(False)
        
        # Date entry
        self.date_entry = ctk.CTkEntry(
            self.entry_frame,
            placeholder_text="YYYY-MM-DD",
            border_width=0,
            fg_color="transparent",
            text_color=SPOTIFY_COLORS["text_bright"]
        )
        self.date_entry.pack(side="left", fill="both", expand=True, padx=(5, 0))
        
        # Calendar button
        try:
            calendar_icon = get_icon_image("calendar", size=16, color=SPOTIFY_COLORS["text_standard"])
            self.calendar_button = ctk.CTkButton(
                self.entry_frame,
                text="",
                width=30,
                height=30,
                corner_radius=0,
                fg_color="transparent",
                hover_color=SPOTIFY_COLORS["accent"],
                image=calendar_icon,
                command=self._show_calendar
            )
        except Exception as e:
            logger.warning(f"Failed to create calendar icon: {e}")
            self.calendar_button = ctk.CTkButton(
                self.entry_frame,
                text="📅",  # Unicode calendar symbol as fallback
                width=30,
                height=30,
                corner_radius=0,
                fg_color="transparent",
                hover_color=SPOTIFY_COLORS["accent"],
                command=self._show_calendar
            )
        self.calendar_button.pack(side="right")
        
        # Set default date
        if default_date:
            self.set(default_date)
        else:
            # Set current date
            from datetime import datetime
            current_date = datetime.now().strftime(self.date_format)
            self.set(current_date)
            
        # Bind validation
        self.date_entry.bind("<FocusOut>", self._validate_date)
        self.date_entry.bind("<Return>", self._validate_date)
    
    def get(self) -> str:
        """
        Get current date.
        
        Returns:
            Current selected date (YYYY-MM-DD format)
        """
        return self.date_entry.get()
        
    def get_date(self) -> tuple:
        """
        Get current date as a tuple of (year, month, day).
        
        Returns:
            Tuple of (year, month, day)
        """
        date_str = self.get()
        try:
            from datetime import datetime
            date_obj = datetime.strptime(date_str, self.date_format)
            return (date_obj.year, date_obj.month, date_obj.day)
        except ValueError:
            # Return current date as fallback
            from datetime import datetime
            now = datetime.now()
            return (now.year, now.month, now.day)
    
    def set(self, date_str: str) -> None:
        """
        Set current date.
        
        Args:
            date_str: Date string (YYYY-MM-DD format)
        """
        if self._is_valid_date(date_str):
            self.date_entry.delete(0, "end")
            self.date_entry.insert(0, date_str)
            if self.command:
                self.command(date_str)
    
    def _validate_date(self, event=None) -> None:
        """
        Validate date entry and reformat if needed.
        
        Args:
            event: Event object
        """
        date_str = self.date_entry.get()
        
        if not date_str:
            # If empty, set current date
            from datetime import datetime
            date_str = datetime.now().strftime(self.date_format)
            self.set(date_str)
            return
            
        # Try to parse and reformat
        if self._is_valid_date(date_str):
            # Already valid, just trigger the command
            if self.command:
                self.command(date_str)
        else:
            # Try alternate formats
            from datetime import datetime
            try:
                # Try MM/DD/YYYY
                date_obj = datetime.strptime(date_str, "%m/%d/%Y")
                formatted = date_obj.strftime(self.date_format)
                self.set(formatted)
            except ValueError:
                try:
                    # Try DD/MM/YYYY
                    date_obj = datetime.strptime(date_str, "%d/%m/%Y")
                    formatted = date_obj.strftime(self.date_format)
                    self.set(formatted)
                except ValueError:
                    # Invalid format, reset to current date
                    date_str = datetime.now().strftime(self.date_format)
                    self.set(date_str)
    
    def _is_valid_date(self, date_str: str) -> bool:
        """
        Check if date string is valid.
        
        Args:
            date_str: Date string to check
            
        Returns:
            True if valid, False otherwise
        """
        from datetime import datetime
        try:
            datetime.strptime(date_str, self.date_format)
            return True
        except ValueError:
            return False
    
    def _show_calendar(self) -> None:
        """Show date picker calendar."""
        # Create popup calendar (simplified version)
        from datetime import datetime
        import logging
        
        logger = logging.getLogger('dockify.ui.components.DateSelector')
        logger.info("Opening date selector calendar")
        
        # Get current date
        try:
            current_date = datetime.strptime(self.get(), self.date_format)
            logger.info(f"Current date: {current_date}")
        except ValueError:
            current_date = datetime.now()
            logger.info(f"Using today's date: {current_date}")
        
        # Рассчитаем позицию окна до его создания
        # Wait for widget to be mapped
        self.update_idletasks()
        
        # Get date selector position
        x = self.winfo_rootx()
        y = self.winfo_rooty() + self.winfo_height()
        
        # Get screen dimensions
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        # Определяем размеры окна календаря заранее
        popup_width = 350
        popup_height = 380
        
        # Adjust position if popup would go off screen
        if x + popup_width > screen_width:
            x = screen_width - popup_width - 10
        
        if y + popup_height > screen_height:
            y = self.winfo_rooty() - popup_height - 10
            if y < 0:  # Если окно выходит за верхнюю границу экрана
                y = 10
        
        # Убедимся, что окно не выходит за левую границу экрана
        if x < 0:
            x = 10
            
        # Логирование позиции для отладки
        logger.info(f"Will position calendar at x={x}, y={y}, width={popup_width}, height={popup_height}")
            
        # Create popup window с уже заданной позицией
        popup = ctk.CTkToplevel(self)
        popup.title("Select Date")
        popup.geometry(f"{popup_width}x{popup_height}+{x}+{y}")  # Сразу задаем и размер, и позицию
        popup.resizable(False, False)
        
        # Важно: сначала отрисовываем окно, потом делаем grab_set
        popup.update_idletasks()
        
        # Add some styling - use a lighter background for better contrast
        popup.configure(fg_color=scale_color(SPOTIFY_COLORS["card_background"], 1.3))
        logger.info("Created popup window with custom styling")
        
        # Month year selector - делаем более контрастным
        month_year_frame = ctk.CTkFrame(popup, fg_color=SPOTIFY_COLORS["accent"], height=50)
        month_year_frame.pack(fill="x", padx=10, pady=10)
        
        # Previous month button
        prev_month_btn = ctk.CTkButton(
            month_year_frame, 
            text="<", 
            width=40,
            height=40,
            image=get_icon_image("chevron-left", 20, SPOTIFY_COLORS["text_bright"]),
            fg_color=lighten_color(SPOTIFY_COLORS["accent"], 0.1),
            hover_color=lighten_color(SPOTIFY_COLORS["accent"], 0.2),
            text_color=SPOTIFY_COLORS["text_bright"],
            command=lambda: change_month(-1)
        )
        prev_month_btn.pack(side="left", padx=10, pady=5)
        
        # Month year label
        month_year_label = ctk.CTkLabel(
            month_year_frame, 
            text=current_date.strftime("%B %Y"),
            font=("Helvetica", 16, "bold"),
            text_color=SPOTIFY_COLORS["text_bright"]
        )
        month_year_label.pack(side="left", expand=True)
        
        # Next month button
        next_month_btn = ctk.CTkButton(
            month_year_frame, 
            text=">", 
            width=40,
            height=40,
            image=get_icon_image("chevron-right", 20, SPOTIFY_COLORS["text_bright"]),
            fg_color=lighten_color(SPOTIFY_COLORS["accent"], 0.1),
            hover_color=lighten_color(SPOTIFY_COLORS["accent"], 0.2),
            text_color=SPOTIFY_COLORS["text_bright"],
            command=lambda: change_month(1)
        )
        next_month_btn.pack(side="right", padx=10, pady=5)
        logger.info("Created month navigation controls")
        
        # Calendar frame - улучшаем контрастность
        cal_frame = ctk.CTkFrame(popup, fg_color=scale_color(SPOTIFY_COLORS["card_background"], 1.2))
        cal_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Weekday headers - делаем более заметными
        weekdays = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
        weekday_frame = ctk.CTkFrame(cal_frame, fg_color=scale_color(SPOTIFY_COLORS["card_background"], 1.3))
        weekday_frame.pack(fill="x", padx=5, pady=5)
        
        for i, day in enumerate(weekdays):
            header = ctk.CTkLabel(
                weekday_frame, 
                text=day,
                font=("Helvetica", 14, "bold"),
                text_color=SPOTIFY_COLORS["accent"],
                width=40
            )
            header.grid(row=0, column=i, padx=3, pady=5)
        logger.info("Created weekday headers")
        
        # Days frame
        days_frame = ctk.CTkFrame(cal_frame, fg_color="transparent")
        days_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Day buttons (will be populated later)
        day_buttons = []
        for row in range(6):  # 6 rows max
            for col in range(7):  # 7 days per week
                btn = ctk.CTkButton(
                    days_frame, 
                    text="", 
                    width=40,
                    height=40,
                    corner_radius=20,
                    fg_color=scale_color(SPOTIFY_COLORS["card_background"], 1.4),
                    hover_color=SPOTIFY_COLORS["accent"],
                    text_color=SPOTIFY_COLORS["text_bright"],
                    font=("Helvetica", 14)
                )
                btn.grid(row=row, column=col, padx=3, pady=3)
                day_buttons.append(btn)
        logger.info(f"Created {len(day_buttons)} day buttons")
        
        # Today button
        today_btn = ctk.CTkButton(
            popup, 
            text="Today",
            font=("Helvetica", 14, "bold"),
            fg_color=SPOTIFY_COLORS["accent_green"],
            hover_color=lighten_color(SPOTIFY_COLORS["accent_green"], 0.1),
            text_color=SPOTIFY_COLORS["text_bright"],
            height=40,
            command=lambda: select_date(datetime.now())
        )
        today_btn.pack(side="bottom", pady=15, padx=10, fill="x")
        
        # Function to select a date
        def select_date(date):
            logger.info(f"Date selected: {date}")
            self.set(date.strftime(self.date_format))
            popup.destroy()
        
        # Function to populate calendar
        def populate_calendar(year, month):
            logger.info(f"Populating calendar for {year}-{month}")
            # Update month year label
            date = datetime(year, month, 1)
            month_year_label.configure(text=date.strftime("%B %Y"))
            
            # Calculate first day of month (0 = Monday, 6 = Sunday)
            first_day = date.replace(day=1).weekday()
            logger.info(f"First day of month falls on weekday {first_day}")
            
            # Calculate days in month
            if month == 12:
                days_in_month = (date.replace(year=year+1, month=1, day=1) - date.replace(day=1)).days
            else:
                days_in_month = (date.replace(month=month+1, day=1) - date.replace(day=1)).days
            logger.info(f"Days in month: {days_in_month}")
            
            # Reset all buttons
            for btn in day_buttons:
                btn.configure(
                    text="", 
                    state="disabled", 
                    fg_color=scale_color(SPOTIFY_COLORS["card_background"], 1.4)
                )
            
            # Populate buttons
            for i in range(days_in_month):
                day = i + 1
                day_date = date.replace(day=day)
                idx = first_day + i
                if idx < len(day_buttons):
                    btn = day_buttons[idx]
                    btn.configure(
                        text=str(day), 
                        state="normal",
                        command=lambda d=day_date: select_date(d)
                    )
                    
                    # Highlight current date
                    if day_date.date() == current_date.date():
                        btn.configure(
                            fg_color=SPOTIFY_COLORS["accent"],
                            text_color=SPOTIFY_COLORS["text_bright"],
                            font=("Helvetica", 14, "bold")
                        )
            
            logger.info(f"Calendar populated with {days_in_month} days")
        
        # Function to change month
        def change_month(delta):
            nonlocal current_date
            year = current_date.year
            month = current_date.month + delta
            
            if month > 12:
                month = 1
                year += 1
            elif month < 1:
                month = 12
                year -= 1
            
            logger.info(f"Changing month by {delta} to {year}-{month}")    
            current_date = current_date.replace(year=year, month=month)
            populate_calendar(year, month)
        
        # Initial population
        populate_calendar(current_date.year, current_date.month)
        
        # Make sure the popup is on top and visible
        popup.lift()
        popup.focus_force()
        popup.update()
        
        # Теперь, когда окно полностью отрисовано, делаем его модальным
        try:
            popup.grab_set()
        except Exception as e:
            logger.error(f"Failed to make calendar popup modal: {e}")
        
        logger.info("Calendar popup initialized and displayed")
        
        # Bind escape key to close popup
        popup.bind("<Escape>", lambda e: popup.destroy())


class TreeView(ctk.CTkFrame):
    """
    Custom tree view widget for file browser.
    """
    def __init__(self, parent, headings: List[str] = [], widths: List[int] = [], 
                 height: int = 400, columns=None, show="headings", selectmode="browse", **kwargs):
        """
        Initialize tree view.
        
        Args:
            parent: Parent widget
            headings: List of column headings
            widths: List of column widths
            height: Height of widget
            columns: Column identifiers (for ttk.Treeview compatibility)
            show: Show option (for ttk.Treeview compatibility)
            selectmode: Selection mode (for ttk.Treeview compatibility)
            **kwargs: Additional arguments for CTkFrame
        """
        # Extract ttk.Treeview specific arguments
        treeview_kwargs = {}
        if columns is not None:
            treeview_kwargs['columns'] = columns
        else:
            treeview_kwargs['columns'] = headings
        
        treeview_kwargs['show'] = show
        treeview_kwargs['selectmode'] = selectmode
        
        # Filter out ttk.Treeview arguments from kwargs
        filtered_kwargs = {k: v for k, v in kwargs.items() 
                          if k not in ['columns', 'show', 'selectmode']}
        
        filtered_kwargs.setdefault("fg_color", SPOTIFY_COLORS["card_background"])
        filtered_kwargs.setdefault("corner_radius", 10)
        
        super().__init__(
            parent,
            height=height,
            **filtered_kwargs
        )
        
        # Store properties
        self.headings = headings or []
        self.widths = widths or []
        self.selection_callback = None
        
        # Create scrollable frame
        self.frame = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            border_width=0
        )
        self.frame.pack(fill="both", expand=True, padx=0, pady=0)
        
        # Create treeview
        self.tree = ttk.Treeview(
            self.frame,
            height=height,
            **treeview_kwargs
        )
        
        # Configure style
        style = ttk.Style()
        
        # Configure column headings
        for i, heading in enumerate(self.headings):
            self.tree.heading(heading, text=heading)
            if i < len(self.widths):
                self.tree.column(heading, width=self.widths[i], minwidth=50)
        
        # Pack
        self.tree.pack(fill="both", expand=True, side="left")
        
        # Scrollbars
        self.vsb = ctk.CTkScrollbar(
            self.frame,
            orientation="vertical",
            command=self.tree.yview
        )
        self.vsb.pack(fill="y", side="right")
        
        # Configure scrollbar
        self.tree.configure(yscrollcommand=self.vsb.set)
        
        # Bind selection event
        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        
    def add_item(self, values: List[Any], tags: List[str] = []) -> str:
        """
        Add an item to the tree.
        
        Args:
            values: List of values for each column
            tags: List of tags to apply
            
        Returns:
            Item ID
        """
        # Insert item
        item_id = self.tree.insert("", "end", values=values, tags=tags or [])
        return item_id
        
    def clear(self) -> None:
        """Clear all items from the tree."""
        for item in self.tree.get_children():
            self.tree.delete(item)
    
    def get_selection(self) -> Optional[str]:
        """
        Get currently selected item ID.
        
        Returns:
            Selected item ID or None
        """
        selection = self.tree.selection()
        if selection:
            return selection[0]
        return None
    
    def get_selection_values(self) -> Optional[List[Any]]:
        """
        Get values of currently selected item.
        
        Returns:
            List of values for selected item or None
        """
        selection = self.tree.selection()
        if selection:
            values = self.tree.item(selection[0], "values")
            # Handle empty values
            if not values:
                return []
            # Convert tuple to list if needed
            if isinstance(values, tuple):
                return list(values)
            return values
        return None
    
    def set_selection_callback(self, callback: Callable[[str], None]) -> None:
        """
        Set callback for selection changes.
        
        Args:
            callback: Function to call with selected item ID
        """
        self.selection_callback = callback
    
    def _on_select(self, event) -> None:
        """
        Handle selection event.
        
        Args:
            event: Selection event
        """
        if self.selection_callback:
            selection = self.tree.selection()
            if selection:
                self.selection_callback(selection[0])
    
    # Forward ttk.Treeview methods
    def heading(self, column, **kwargs):
        """Forward heading method to underlying ttk.Treeview."""
        return self.tree.heading(column, **kwargs)
    
    def column(self, column, **kwargs):
        """Forward column method to underlying ttk.Treeview."""
        return self.tree.column(column, **kwargs)
    
    def insert(self, parent, index, **kwargs):
        """Forward insert method to underlying ttk.Treeview."""
        return self.tree.insert(parent, index, **kwargs)
    
    def delete(self, *items):
        """Forward delete method to underlying ttk.Treeview."""
        return self.tree.delete(*items)
    
    def get_children(self, item=""):
        """Forward get_children method to underlying ttk.Treeview."""
        return self.tree.get_children(item)
    
    def selection(self):
        """Forward selection method to underlying ttk.Treeview."""
        return self.tree.selection()
    
    def item(self, item, option=None, **kwargs):
        """Forward item method to underlying ttk.Treeview."""
        return self.tree.item(item, option, **kwargs)
    
    def tree_bind(self, sequence=None, func=None, add=None):
        """Forward bind method to underlying ttk.Treeview."""
        return self.tree.bind(sequence, func, add)