"""
Theme utilities for Dockify.
Defines colors, styling functions, and theme-related utilities for the application.
"""
import logging
import tkinter as tk
from typing import Dict, Any, Optional

logger = logging.getLogger('dockify.utils.theme')

# Spotify-inspired color palette
SPOTIFY_COLORS = {
    # Main colors
    "background": "#121212",  # Main app background
    "card_background": "#181818",  # Card/panel background
    "accent": "#1DB954",  # Primary accent (Spotify green)
    
    # Text colors
    "text_bright": "#FFFFFF",  # Bright text
    "text_standard": "#B3B3B3",  # Standard text
    "text_subtle": "#727272",  # Subtle/muted text
    
    # Accent colors
    "accent_green": "#1DB954",  # Success, positive actions
    "accent_red": "#E91429",  # Error, delete actions
    "accent_orange": "#FF9800",  # Warning, caution
    "accent_blue": "#4285F4",  # Info, links
    "accent_purple": "#9C27B0",  # Secondary accent
    "accent_yellow": "#FFCA28",  # Highlights
    
    # UI elements
    "border": "#333333",  # Border color
    "hover": "#282828",  # Hover state
    "selection": "#262626",  # Selected item
}

def apply_theme(root):
    """
    Apply the Spotify-inspired theme to the application.
    
    Args:
        root: The root or toplevel window
    """
    try:
        # Configure tkinter styles
        style = tk.ttk.Style()
        
        # Configure ttk styles
        style.configure("TButton", 
                       background=SPOTIFY_COLORS["accent"],
                       foreground=SPOTIFY_COLORS["text_bright"],
                       padding=8,
                       font=("Helvetica", 11))
        
        style.map("TButton",
                 background=[("active", lighten_color(SPOTIFY_COLORS["accent"], 0.1))],
                 foreground=[("active", SPOTIFY_COLORS["text_bright"])])
        
        style.configure("TLabel", 
                       background=SPOTIFY_COLORS["background"],
                       foreground=SPOTIFY_COLORS["text_standard"],
                       font=("Helvetica", 11))
        
        # Configure ttk.Treeview
        style.configure("Treeview", 
                      background=SPOTIFY_COLORS["card_background"],
                      foreground=SPOTIFY_COLORS["text_bright"],
                      fieldbackground=SPOTIFY_COLORS["card_background"],
                      font=("Helvetica", 11))
        
        style.configure("Treeview.Heading", 
                      background=SPOTIFY_COLORS["card_background"],
                      foreground=SPOTIFY_COLORS["text_subtle"],
                      font=("Helvetica", 12, "bold"))
        
        style.map("Treeview", 
                background=[("selected", SPOTIFY_COLORS["accent"])],
                foreground=[("selected", SPOTIFY_COLORS["text_bright"])])
        
        # Other configurations as needed
        logger.info("Applied Spotify-inspired theme to the application")
        
    except Exception as e:
        logger.error(f"Error applying theme: {e}")


def lighten_color(color: str, factor: float = 0.2) -> str:
    """
    Lighten a hex color by a factor.
    
    Args:
        color: Hex color string (e.g., "#1DB954")
        factor: Lightening factor (0.0 to 1.0)
        
    Returns:
        Lightened hex color string
    """
    # Make sure color is a valid hex string
    if not color.startswith('#') or len(color) != 7:
        logger.warning(f"Invalid color format: {color}")
        return color
    
    try:
        # Convert hex to RGB
        r = int(color[1:3], 16)
        g = int(color[3:5], 16)
        b = int(color[5:7], 16)
        
        # Lighten each component
        r = min(255, int(r + (255 - r) * factor))
        g = min(255, int(g + (255 - g) * factor))
        b = min(255, int(b + (255 - b) * factor))
        
        # Convert back to hex
        return f"#{r:02x}{g:02x}{b:02x}"
    except Exception as e:
        logger.error(f"Error lightening color {color}: {e}")
        return color


def darken_color(color: str, factor: float = 0.2) -> str:
    """
    Darken a hex color by a factor.
    
    Args:
        color: Hex color string (e.g., "#1DB954")
        factor: Darkening factor (0.0 to 1.0)
        
    Returns:
        Darkened hex color string
    """
    # Make sure color is a valid hex string
    if not color.startswith('#') or len(color) != 7:
        logger.warning(f"Invalid color format: {color}")
        return color
    
    try:
        # Convert hex to RGB
        r = int(color[1:3], 16)
        g = int(color[3:5], 16)
        b = int(color[5:7], 16)
        
        # Darken each component
        r = max(0, int(r * (1 - factor)))
        g = max(0, int(g * (1 - factor)))
        b = max(0, int(b * (1 - factor)))
        
        # Convert back to hex
        return f"#{r:02x}{g:02x}{b:02x}"
    except Exception as e:
        logger.error(f"Error darkening color {color}: {e}")
        return color


def scale_color(color: str, factor: float = 1.0, opacity: float = 1.0) -> str:
    """
    Scale a hex color by a factor and optionally adjust opacity.
    
    Args:
        color: Hex color string (e.g., "#1DB954")
        factor: Scaling factor (lighter > 1.0, darker < 1.0)
        opacity: Opacity factor (0.0 to 1.0, only affects appearance)
        
    Returns:
        Scaled hex color string
    """
    # Make sure color is a valid hex string
    if not color.startswith('#') or len(color) != 7:
        logger.warning(f"Invalid color format: {color}")
        return color
    
    try:
        # Convert hex to RGB
        r = int(color[1:3], 16)
        g = int(color[3:5], 16)
        b = int(color[5:7], 16)
        
        # Scale each component
        if factor > 1.0:
            # Lighten
            r = min(255, int(r + (255 - r) * (factor - 1.0)))
            g = min(255, int(g + (255 - g) * (factor - 1.0)))
            b = min(255, int(b + (255 - b) * (factor - 1.0)))
        elif factor < 1.0:
            # Darken
            r = max(0, int(r * factor))
            g = max(0, int(g * factor))
            b = max(0, int(b * factor))
        
        # Apply opacity (this just simulates opacity for our theme calculations)
        if opacity < 1.0:
            bg_color = int(SPOTIFY_COLORS["background"][1:3], 16)
            r = int(r * opacity + bg_color * (1 - opacity))
            g = int(g * opacity + bg_color * (1 - opacity))
            b = int(b * opacity + bg_color * (1 - opacity))
        
        # Convert back to hex
        return f"#{r:02x}{g:02x}{b:02x}"
    except Exception as e:
        logger.error(f"Error scaling color {color}: {e}")
        return color


def get_font(size: int, bold: bool = False) -> tuple:
    """
    Get a font tuple for consistent typography.
    
    Args:
        size: Font size
        bold: Whether to use bold weight
        
    Returns:
        Font tuple (family, size, weight)
    """
    weight = "bold" if bold else "normal"
    return ("Helvetica", size, weight)
