import json
import os
import logging
import tkinter as tk
from tkinter import ttk, messagebox

# Using absolute path for configuration file
CONFIG_PATH = os.path.join(os.path.expanduser("~"), ".reimdockify", "config.json")

logger = logging.getLogger('reimdockify.ui.settings')

class SettingsDialog(tk.Toplevel):
    def __init__(self, parent, apply_callback):
        super().__init__(parent)
        self.title("Settings")
        self.minsize(400, 200)
        # Center window over parent
        self.update_idletasks()
        w = self.winfo_reqwidth()
        h = self.winfo_reqheight()
        px = self.master.winfo_x()
        py = self.master.winfo_y()
        pw = self.master.winfo_width()
        ph = self.master.winfo_height()
        x = px + (pw - w)//2
        y = py + (ph - h)//2
        self.geometry(f"{w}x{h}+{x}+{y}")

        self.apply_callback = apply_callback

        # Load existing or defaults
        self.load_config()

        # Poll interval
        ttk.Label(self, text="Poll Interval (sec):").grid(row=0, column=0, sticky='w', padx=10, pady=5)
        self.poll_var = tk.IntVar(value=self.cfg['poll_interval'])
        ttk.Entry(self, textvariable=self.poll_var, width=10).grid(row=0, column=1, sticky='w', padx=10, pady=5)
        
        # Auto-adjust interval
        self.auto_adjust_var = tk.BooleanVar(value=self.cfg.get('auto_adjust_interval', True))
        ttk.Checkbutton(self, text="Automatically adjust interval when collection is slow", 
                      variable=self.auto_adjust_var).grid(row=1, columnspan=2, sticky='w', padx=10, pady=5)

        # Docker socket
        ttk.Label(self, text="Docker socket path:").grid(row=2, column=0, sticky='w', padx=10, pady=5)
        self.socket_var = tk.StringVar(value=self.cfg['docker_socket'])
        ttk.Entry(self, textvariable=self.socket_var, width=30).grid(row=2, column=1, sticky='w', padx=10, pady=5)

        # Enable alerts
        self.alerts_var = tk.BooleanVar(value=self.cfg['enable_alerts'])
        ttk.Checkbutton(self, text="Enable popup notifications", variable=self.alerts_var).grid(row=3, columnspan=2, sticky='w', padx=10, pady=5)

        # Buttons
        btn_frame = ttk.Frame(self)
        btn_frame.grid(row=4, columnspan=2, pady=10)
        ttk.Button(btn_frame, text="Save", command=self.on_save).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self.destroy).pack(side="right", padx=5)
        
        logger.info("Settings dialog initialized")

    def load_config(self):
        """Load settings from configuration file or use default values."""
        try:
            # Make sure the directory exists
            os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
            
            if os.path.exists(CONFIG_PATH):
                with open(CONFIG_PATH, 'r') as f:
                    self.cfg = json.load(f)
                    logger.info(f"Loaded settings from {CONFIG_PATH}")
            else:
                self.cfg = {
                    'poll_interval': 5, 
                    'docker_socket': '/var/run/docker.sock', 
                    'enable_alerts': True,
                    'auto_adjust_interval': True
                }
                logger.info("Using default settings")
                
            # Check for all required settings
            if 'poll_interval' not in self.cfg:
                self.cfg['poll_interval'] = 5
            if 'docker_socket' not in self.cfg:
                self.cfg['docker_socket'] = '/var/run/docker.sock'
            if 'enable_alerts' not in self.cfg:
                self.cfg['enable_alerts'] = True
            if 'auto_adjust_interval' not in self.cfg:
                self.cfg['auto_adjust_interval'] = True
                
        except Exception as e:
            logger.error(f"Error loading settings: {e}")
            self.cfg = {
                'poll_interval': 5, 
                'docker_socket': '/var/run/docker.sock', 
                'enable_alerts': True,
                'auto_adjust_interval': True
            }

    def on_save(self):
        """Save settings and apply them."""
        try:
            # Get values from fields
            poll_interval = self.poll_var.get()
            docker_socket = self.socket_var.get()
            enable_alerts = self.alerts_var.get()
            auto_adjust_interval = self.auto_adjust_var.get()
            
            # Check for valid values
            if poll_interval < 1:
                poll_interval = 1
                messagebox.showwarning("Invalid Value", "Poll interval cannot be less than 1 second. Set to 1.")
            
            if not docker_socket:
                docker_socket = '/var/run/docker.sock'
                messagebox.showwarning("Invalid Value", "Docker socket path cannot be empty. Using default value.")
            
            # Create configuration
            self.cfg = {
                'poll_interval': poll_interval,
                'docker_socket': docker_socket,
                'enable_alerts': enable_alerts,
                'auto_adjust_interval': auto_adjust_interval
            }
            
            # Save to file
            os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
            with open(CONFIG_PATH, 'w') as f:
                json.dump(self.cfg, f, indent=2)
            
            logger.info(f"Saved settings to {CONFIG_PATH}: {self.cfg}")
            
            # Apply settings
            self.apply_callback(self.cfg)
            
            messagebox.showinfo("Settings", "Settings saved successfully")
            self.destroy()
            
        except Exception as e:
            logger.error(f"Error saving settings: {e}")
            messagebox.showerror("Error", f"Failed to save settings: {e}")
