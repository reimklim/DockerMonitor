"""
Sidebar navigation frame for ReimDockify.
"""
import logging
import tkinter as tk
from typing import Dict, List, Any, Optional, Callable

import customtkinter as ctk

from utils.theme import SPOTIFY_COLORS, lighten_color, scale_color
from assets.icons import get_icon_image

logger = logging.getLogger('reimdockify.ui.sidebar')

class SidebarFrame(ctk.CTkFrame):
    """
    Sidebar navigation frame with Spotify-inspired styling.
    """
    def __init__(self, parent):
        """
        Initialize the sidebar frame.
        
        Args:
            parent: Parent widget
        """
        super().__init__(
            parent,
            width=200,
            fg_color=scale_color(SPOTIFY_COLORS["background"], 0.9),  # Slightly darker than main background
            corner_radius=0
        )
        
        # Force width to remain constant
        self.pack_propagate(False)
        
        # Create UI
        self.create_ui()
        
    def create_ui(self):
        """Create and setup the user interface."""
        # App logo/name
        self.logo_frame = ctk.CTkFrame(self, fg_color="transparent", height=120)
        self.logo_frame.pack(fill="x", padx=0, pady=0)
        
        # App name
        self.app_name = ctk.CTkLabel(
            self.logo_frame,
            text="ReimDockify",
            font=("Helvetica", 24, "bold"),
            text_color=SPOTIFY_COLORS["text_bright"]
        )
        self.app_name.place(relx=0.5, rely=0.5, anchor="center")
        
        # Navigation menu
        self.nav_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.nav_frame.pack(fill="x", padx=10, pady=(20, 0))
        
        # Navigation buttons
        self.btn_overview = self.create_nav_button("Overview", "overview")
        self.btn_containers = self.create_nav_button("Containers", "containers")
        self.btn_metrics = self.create_nav_button("Metrics", "metrics")
        self.btn_reports = self.create_nav_button("Reports", "reports")
        self.btn_code = self.create_nav_button("Code Explorer", "code")
        
        # Bottom section for settings etc.
        self.bottom_frame = ctk.CTkFrame(self, fg_color="transparent", height=100)
        self.bottom_frame.pack(fill="x", side="bottom", padx=10, pady=10)
        
        # Settings button
        try:
            settings_icon = get_icon_image("settings", size=16, color=SPOTIFY_COLORS["text_subtle"])
            self.btn_settings = ctk.CTkButton(
                self.bottom_frame,
                text="Settings",
                font=("Helvetica", 12),
                fg_color="transparent",
                hover_color=scale_color(SPOTIFY_COLORS["background"], 1.1),
                text_color=SPOTIFY_COLORS["text_subtle"],
                anchor="w",
                image=settings_icon,
                compound="left"
            )
        except Exception as e:
            logger.warning(f"Failed to create settings button with icon: {e}")
            self.btn_settings = ctk.CTkButton(
                self.bottom_frame,
                text="Settings",
                font=("Helvetica", 12),
                fg_color="transparent",
                hover_color=scale_color(SPOTIFY_COLORS["background"], 1.1),
                text_color=SPOTIFY_COLORS["text_subtle"],
                anchor="w"
            )
        self.btn_settings.pack(fill="x", pady=5)
        
        # Logout button
        try:
            logout_icon = get_icon_image("log-out", size=16, color=SPOTIFY_COLORS["accent_red"])
            self.btn_logout = ctk.CTkButton(
                self.bottom_frame,
                text="Logout",
                font=("Helvetica", 12),
                fg_color="transparent",
                hover_color=scale_color(SPOTIFY_COLORS["background"], 1.1),
                text_color=SPOTIFY_COLORS["accent_red"],
                anchor="w",
                image=logout_icon,
                compound="left"
            )
        except Exception as e:
            logger.warning(f"Failed to create logout button with icon: {e}")
            self.btn_logout = ctk.CTkButton(
                self.bottom_frame,
                text="Logout",
                font=("Helvetica", 12),
                fg_color="transparent",
                hover_color=scale_color(SPOTIFY_COLORS["background"], 1.1),
                text_color=SPOTIFY_COLORS["accent_red"],
                anchor="w"
            )
        self.btn_logout.pack(fill="x", pady=5)
        
    def create_nav_button(self, text: str, icon_name: str) -> ctk.CTkButton:
        """
        Create a navigation button.
        
        Args:
            text: Button text
            icon_name: Icon name
            
        Returns:
            Navigation button
        """
        try:
            # Пытаемся получить изображение
            icon_img = get_icon_image(icon_name, size=20, color=SPOTIFY_COLORS["text_standard"])
            
            button = ctk.CTkButton(
                self.nav_frame,
                text=text,
                font=("Helvetica", 14),
                fg_color="transparent",
                hover_color=scale_color(SPOTIFY_COLORS["background"], 1.1),
                text_color=SPOTIFY_COLORS["text_standard"],
                anchor="w",
                image=icon_img,
                compound="left",
                height=40
            )
        except Exception as e:
            # В случае ошибки создаем кнопку без изображения
            logger.warning(f"Failed to create button with icon {icon_name}: {e}")
            button = ctk.CTkButton(
                self.nav_frame,
                text=text,
                font=("Helvetica", 14),
                fg_color="transparent",
                hover_color=scale_color(SPOTIFY_COLORS["background"], 1.1),
                text_color=SPOTIFY_COLORS["text_standard"],
                anchor="w",
                height=40
            )
            
        button.pack(fill="x", pady=5)
        
        return button
        
    def set_active(self, button: ctk.CTkButton) -> None:
        """
        Set a button as active.
        
        Args:
            button: Button to set as active
        """
        # Reset all buttons
        for btn in [self.btn_overview, self.btn_containers, self.btn_metrics, 
                    self.btn_reports, self.btn_code]:
            btn.configure(
                fg_color="transparent", 
                text_color=SPOTIFY_COLORS["text_standard"]
            )
            
        # Set active button - using green color for highlighting
        button.configure(
            fg_color=SPOTIFY_COLORS["accent_green"],
            text_color=SPOTIFY_COLORS["text_bright"]
        )