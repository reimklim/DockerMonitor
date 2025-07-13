"""
Login window.
"""
import logging
import tkinter as tk
from typing import Callable, Optional

import customtkinter as ctk

from db.database import get_db_session
from db.services.user_service import UserService
from utils.theme import SPOTIFY_COLORS, lighten_color, scale_color
from assets.icons import get_icon_image

logger = logging.getLogger('reimdockify.ui.auth.login')


class LoginWindow(ctk.CTkToplevel):
    """Login window."""
    
    def __init__(self, parent, on_login: Callable[[int], None], on_register: Callable = None):
        """
        Initialize the login window.
        
        Args:
            parent: Parent widget
            on_login: Callback function for successful login
            on_register: Callback function for registration
        """
        super().__init__(parent)
        self.title("ReimDockify - Login")
        self.geometry("400x500")
        self.resizable(False, False)
        
        # Center the window on the main screen
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width // 2) - 200  # Half of window width (400/2)
        y = (screen_height // 2) - 250  # Half of window height (500/2)
        self.geometry(f"400x500+{x}+{y}")
        
        # Configure window close protocol
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Save callbacks
        self.on_login = on_login
        self.on_register = on_register
        
        # Create UI
        self.create_ui()
        
        # Make window modal
        self.grab_set()
        self.focus_set()
        
    def create_ui(self):
        """Create UI elements."""
        # Main container
        self.main_frame = ctk.CTkFrame(self, fg_color=SPOTIFY_COLORS["background"])
        self.main_frame.pack(fill="both", expand=True)
        
        # Logo
        self.logo_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.logo_frame.pack(fill="x", padx=20, pady=(30, 10))
        
        self.logo_label = ctk.CTkLabel(
            self.logo_frame,
            text="ReimDockify",
            font=("Helvetica", 36, "bold"),
            text_color=SPOTIFY_COLORS["accent"]
        )
        self.logo_label.pack()
        
        self.subtitle_label = ctk.CTkLabel(
            self.logo_frame,
            text="Docker Container Monitor",
            font=("Helvetica", 14),
            text_color=SPOTIFY_COLORS["text_subtle"]
        )
        self.subtitle_label.pack(pady=(0, 5))
        
        # Login form
        self.form_frame = ctk.CTkFrame(
            self.main_frame,
            fg_color=scale_color(SPOTIFY_COLORS["card_background"], 1.1),
            corner_radius=10
        )
        self.form_frame.pack(fill="x", padx=20, pady=10)
        
        # Form title
        self.form_title = ctk.CTkLabel(
            self.form_frame,
            text="Login",
            font=("Helvetica", 16, "bold"),
            text_color=SPOTIFY_COLORS["text_bright"]
        )
        self.form_title.pack(pady=(15, 5))
        
        # Username field
        self.username_frame = ctk.CTkFrame(self.form_frame, fg_color="transparent")
        self.username_frame.pack(fill="x", padx=20, pady=(5, 5))
        
        self.username_label = ctk.CTkLabel(
            self.username_frame,
            text="Username or Email",
            font=("Helvetica", 12),
            text_color=SPOTIFY_COLORS["text_standard"],
            anchor="w"
        )
        self.username_label.pack(fill="x")
        
        self.username_entry = ctk.CTkEntry(
            self.username_frame,
            placeholder_text="Enter username or email",
            height=36,
            border_width=1,
            border_color=scale_color(SPOTIFY_COLORS["card_background"], 1.3),
            fg_color=scale_color(SPOTIFY_COLORS["card_background"], 1.2),
            text_color=SPOTIFY_COLORS["text_bright"]
        )
        self.username_entry.pack(fill="x", pady=(5, 0))
        
        # Password field
        self.password_frame = ctk.CTkFrame(self.form_frame, fg_color="transparent")
        self.password_frame.pack(fill="x", padx=20, pady=(5, 5))
        
        self.password_label = ctk.CTkLabel(
            self.password_frame,
            text="Password",
            font=("Helvetica", 12),
            text_color=SPOTIFY_COLORS["text_standard"],
            anchor="w"
        )
        self.password_label.pack(fill="x")
        
        self.password_entry = ctk.CTkEntry(
            self.password_frame,
            placeholder_text="Enter password",
            height=36,
            border_width=1,
            border_color=scale_color(SPOTIFY_COLORS["card_background"], 1.3),
            fg_color=scale_color(SPOTIFY_COLORS["card_background"], 1.2),
            text_color=SPOTIFY_COLORS["text_bright"],
            show="●"
        )
        self.password_entry.pack(fill="x", pady=(5, 0))
        
        # Error message
        self.error_label = ctk.CTkLabel(
            self.form_frame,
            text="",
            font=("Helvetica", 12),
            text_color=SPOTIFY_COLORS["accent_red"],
            anchor="center"
        )
        self.error_label.pack(fill="x", padx=20, pady=(5, 0))
        
        # Login button
        self.login_button = ctk.CTkButton(
            self.form_frame,
            text="Login",
            font=("Helvetica", 14, "bold"),
            height=40,
            fg_color=SPOTIFY_COLORS["accent"],
            hover_color=lighten_color(SPOTIFY_COLORS["accent"], 0.1),
            text_color=SPOTIFY_COLORS["text_bright"],
            command=self.login
        )
        self.login_button.pack(fill="x", padx=20, pady=(10, 15))
        
        # Registration link at bottom of form
        self.register_frame = ctk.CTkFrame(self.form_frame, fg_color="transparent")
        self.register_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        # Create link as text, centered
        self.register_link = ctk.CTkLabel(
            self.register_frame,
            text="No account? Register",
            font=("Helvetica", 12),
            text_color=SPOTIFY_COLORS["accent_green"],
            cursor="hand2"
        )
        self.register_link.pack(anchor="center")
        self.register_link.bind("<Button-1>", self.show_register)
        
        # Demo mode button
        self.demo_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent") 
        self.demo_frame.pack(fill="x", padx=20, pady=10)
        
        self.demo_button = ctk.CTkButton(
            self.demo_frame,
            text="Launch in demo mode",
            font=("Helvetica", 12),
            height=30,
            fg_color=SPOTIFY_COLORS["card_background"],
            hover_color=scale_color(SPOTIFY_COLORS["card_background"], 1.2),
            text_color=SPOTIFY_COLORS["text_standard"],
            command=self.start_demo_mode
        )
        self.demo_button.pack(fill="x")
        
        # Bind Enter to login button
        self.username_entry.bind("<Return>", lambda e: self.login())
        self.password_entry.bind("<Return>", lambda e: self.login())
        
        # Focus on username field
        self.username_entry.focus_set()
        
    def login(self):
        """Login handler."""
        # Clear error message
        self.error_label.configure(text="")
        
        # Get data from input fields
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        
        # Check if fields are empty
        if not username:
            self.error_label.configure(text="Enter username or email")
            self.username_entry.focus_set()
            return
        
        if not password:
            self.error_label.configure(text="Enter password")
            self.password_entry.focus_set()
            return
        
        # Authenticate user
        try:
            db_session = get_db_session()
            user_service = UserService(db_session)
            user = user_service.authenticate_user(username, password)
            
            if user:
                logger.info(f"User {username} logged in successfully")
                # Call callback with user ID
                self.on_login(user.id)
                # Close window
                self.destroy()
            else:
                logger.warning(f"Failed login attempt for user {username}")
                self.error_label.configure(text="Invalid username or password")
                self.password_entry.delete(0, "end")
                self.password_entry.focus_set()
        except Exception as e:
            logger.error(f"Error during login: {e}")
            self.error_label.configure(text="Login error")
        
    def show_register(self, event=None):
        """Show registration window."""
        if self.on_register:
            self.on_register()
            self.destroy()
    
    def start_demo_mode(self):
        """Launch application in demo mode."""
        # Call callback with user ID 0 (demo mode)
        self.on_login(0)
        # Close window
        self.destroy()
    
    def on_close(self):
        """Close window handler."""
        # If window is closed without login, exit application
        self.master.destroy() 