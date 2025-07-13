"""
User registration window.
"""
import logging
import tkinter as tk
from typing import Callable, Optional

import customtkinter as ctk

from db.database import get_db_session
from db.services.user_service import UserService
from utils.theme import SPOTIFY_COLORS, lighten_color, scale_color
from assets.icons import get_icon_image

logger = logging.getLogger('reimdockify.ui.auth.register')


class RegisterWindow(ctk.CTkToplevel):
    """User registration window."""
    
    def __init__(self, parent, on_register: Callable[[int], None], on_login: Callable = None):
        """
        Initialize registration window.
        
        Args:
            parent: Parent widget
            on_register: Callback function for successful registration
            on_login: Callback function to return to login
        """
        super().__init__(parent)
        self.title("ReimDockify - Registration")
        self.geometry("400x680")  # Increased height
        self.resizable(False, False)
        
        # Center window on main screen
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width // 2) - 200  # Half of window width (400/2)
        y = (screen_height // 2) - 340  # Half of window height (680/2)
        self.geometry(f"400x680+{x}+{y}")
        
        # Configure window close protocol
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Save callbacks
        self.on_register = on_register
        self.on_login = on_login
        
        # Create UI
        self.create_ui()
        
        # Make window modal
        self.grab_set()
        self.focus_set()
        
    def create_ui(self):
        """Create UI elements."""
        # Main container without scrolling
        self.main_frame = ctk.CTkFrame(self, fg_color=SPOTIFY_COLORS["background"])
        self.main_frame.pack(fill="both", expand=True)
        
        # Logo
        self.logo_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.logo_frame.pack(fill="x", padx=20, pady=(20, 10))
        
        self.logo_label = ctk.CTkLabel(
            self.logo_frame,
            text="ReimDockify",
            font=("Helvetica", 30, "bold"),
            text_color=SPOTIFY_COLORS["accent"]
        )
        self.logo_label.pack()
        
        self.subtitle_label = ctk.CTkLabel(
            self.logo_frame,
            text="Create an Account",
            font=("Helvetica", 14),
            text_color=SPOTIFY_COLORS["text_subtle"]
        )
        self.subtitle_label.pack(pady=(0, 5))
        
        # Registration form
        self.form_frame = ctk.CTkFrame(
            self.main_frame,
            fg_color=scale_color(SPOTIFY_COLORS["card_background"], 1.1),
            corner_radius=10
        )
        self.form_frame.pack(fill="x", padx=20, pady=10)
        
        # Username field
        self.username_frame = ctk.CTkFrame(self.form_frame, fg_color="transparent")
        self.username_frame.pack(fill="x", padx=20, pady=(15, 5))
        
        self.username_label = ctk.CTkLabel(
            self.username_frame,
            text="Username",
            font=("Helvetica", 12),
            text_color=SPOTIFY_COLORS["text_standard"],
            anchor="w"
        )
        self.username_label.pack(fill="x")
        
        self.username_entry = ctk.CTkEntry(
            self.username_frame,
            placeholder_text="Enter username",
            height=36,
            border_width=1,
            border_color=scale_color(SPOTIFY_COLORS["card_background"], 1.3),
            fg_color=scale_color(SPOTIFY_COLORS["card_background"], 1.2),
            text_color=SPOTIFY_COLORS["text_bright"]
        )
        self.username_entry.pack(fill="x", pady=(5, 0))
        
        # Email field
        self.email_frame = ctk.CTkFrame(self.form_frame, fg_color="transparent")
        self.email_frame.pack(fill="x", padx=20, pady=(10, 5))
        
        self.email_label = ctk.CTkLabel(
            self.email_frame,
            text="Email",
            font=("Helvetica", 12),
            text_color=SPOTIFY_COLORS["text_standard"],
            anchor="w"
        )
        self.email_label.pack(fill="x")
        
        self.email_entry = ctk.CTkEntry(
            self.email_frame,
            placeholder_text="Enter email",
            height=36,
            border_width=1,
            border_color=scale_color(SPOTIFY_COLORS["card_background"], 1.3),
            fg_color=scale_color(SPOTIFY_COLORS["card_background"], 1.2),
            text_color=SPOTIFY_COLORS["text_bright"]
        )
        self.email_entry.pack(fill="x", pady=(5, 0))
        
        # Full name field
        self.fullname_frame = ctk.CTkFrame(self.form_frame, fg_color="transparent")
        self.fullname_frame.pack(fill="x", padx=20, pady=(10, 5))
        
        self.fullname_label = ctk.CTkLabel(
            self.fullname_frame,
            text="Full Name (optional)",
            font=("Helvetica", 12),
            text_color=SPOTIFY_COLORS["text_standard"],
            anchor="w"
        )
        self.fullname_label.pack(fill="x")
        
        self.fullname_entry = ctk.CTkEntry(
            self.fullname_frame,
            placeholder_text="Enter full name",
            height=36,
            border_width=1,
            border_color=scale_color(SPOTIFY_COLORS["card_background"], 1.3),
            fg_color=scale_color(SPOTIFY_COLORS["card_background"], 1.2),
            text_color=SPOTIFY_COLORS["text_bright"]
        )
        self.fullname_entry.pack(fill="x", pady=(5, 0))
        
        # Password field
        self.password_frame = ctk.CTkFrame(self.form_frame, fg_color="transparent")
        self.password_frame.pack(fill="x", padx=20, pady=(10, 5))
        
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
        
        # Confirm password field
        self.confirm_password_frame = ctk.CTkFrame(self.form_frame, fg_color="transparent")
        self.confirm_password_frame.pack(fill="x", padx=20, pady=(10, 5))
        
        self.confirm_password_label = ctk.CTkLabel(
            self.confirm_password_frame,
            text="Confirm Password",
            font=("Helvetica", 12),
            text_color=SPOTIFY_COLORS["text_standard"],
            anchor="w"
        )
        self.confirm_password_label.pack(fill="x")
        
        self.confirm_password_entry = ctk.CTkEntry(
            self.confirm_password_frame,
            placeholder_text="Confirm password",
            height=36,
            border_width=1,
            border_color=scale_color(SPOTIFY_COLORS["card_background"], 1.3),
            fg_color=scale_color(SPOTIFY_COLORS["card_background"], 1.2),
            text_color=SPOTIFY_COLORS["text_bright"],
            show="●"
        )
        self.confirm_password_entry.pack(fill="x", pady=(5, 0))
        
        # Error message
        self.error_label = ctk.CTkLabel(
            self.form_frame,
            text="",
            font=("Helvetica", 12),
            text_color=SPOTIFY_COLORS["accent_red"],
            anchor="center"
        )
        self.error_label.pack(fill="x", padx=20, pady=(10, 0))
        
        # Register button
        self.register_button = ctk.CTkButton(
            self.form_frame,
            text="Register",
            font=("Helvetica", 14, "bold"),
            height=40,
            fg_color=SPOTIFY_COLORS["accent"],
            hover_color=lighten_color(SPOTIFY_COLORS["accent"], 0.1),
            text_color=SPOTIFY_COLORS["text_bright"],
            command=self.register
        )
        self.register_button.pack(fill="x", padx=20, pady=(10, 10))
        
        # Login link
        self.login_frame = ctk.CTkFrame(self.form_frame, fg_color="transparent")
        self.login_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        # Create a clickable link in the center
        self.login_link = ctk.CTkLabel(
            self.login_frame,
            text="Already have an account? Login",
            font=("Helvetica", 12),
            text_color=SPOTIFY_COLORS["accent_green"],
            cursor="hand2"
        )
        self.login_link.pack(anchor="center")
        self.login_link.bind("<Button-1>", self.show_login)
        
        # Bind Enter to register button
        self.username_entry.bind("<Return>", lambda e: self.register())
        self.email_entry.bind("<Return>", lambda e: self.register())
        self.fullname_entry.bind("<Return>", lambda e: self.register())
        self.password_entry.bind("<Return>", lambda e: self.register())
        self.confirm_password_entry.bind("<Return>", lambda e: self.register())
        
        # Focus on username field
        self.username_entry.focus_set()
        
    def register(self):
        """Registration handler."""
        # Clear error message
        self.error_label.configure(text="")
        
        # Get data from input fields
        username = self.username_entry.get().strip()
        email = self.email_entry.get().strip()
        full_name = self.fullname_entry.get().strip()
        password = self.password_entry.get()
        confirm_password = self.confirm_password_entry.get()
        
        # Check that required fields are not empty
        if not username:
            self.error_label.configure(text="Enter username")
            self.username_entry.focus_set()
            return
        
        if not email:
            self.error_label.configure(text="Enter email")
            self.email_entry.focus_set()
            return
        
        if not password:
            self.error_label.configure(text="Enter password")
            self.password_entry.focus_set()
            return
        
        if not confirm_password:
            self.error_label.configure(text="Confirm password")
            self.confirm_password_entry.focus_set()
            return
        
        # Check that passwords match
        if password != confirm_password:
            self.error_label.configure(text="Passwords do not match")
            self.confirm_password_entry.delete(0, "end")
            self.confirm_password_entry.focus_set()
            return
        
        # Check password length
        if len(password) < 6:
            self.error_label.configure(text="Password must contain at least 6 characters")
            self.password_entry.focus_set()
            return
        
        # Register user
        try:
            db_session = get_db_session()
            user_service = UserService(db_session)
            
            # If full_name is empty, pass None
            full_name = full_name if full_name else None
            
            user = user_service.create_user(username, email, password, full_name)
            
            if user:
                logger.info(f"User {username} registered successfully")
                # Call callback with user ID
                self.on_register(user.id)
                # Close window
                self.destroy()
            else:
                logger.warning(f"Failed to register user {username}")
                self.error_label.configure(text="User with this name or email already exists")
        except Exception as e:
            logger.error(f"Error during registration: {e}")
            self.error_label.configure(text="Registration error")
        
    def show_login(self, event=None):
        """Show login window."""
        if self.on_login:
            self.on_login()
            self.destroy()
    
    def on_close(self):
        """Close window handler."""
        # If window is closed without registration, end the application
        self.master.destroy() 