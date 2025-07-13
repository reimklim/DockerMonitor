"""
Configuration management for Dockify.
Handles loading, saving, and accessing application configuration settings.
"""
import os
import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger('dockify.utils.config')

class AppConfig:
    """
    Manages application configuration settings.
    """
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration manager.
        
        Args:
            config_path: Path to configuration file (optional)
        """
        # Default configuration path in user's home directory
        if config_path is None:
            self.config_path = os.path.join(
                os.path.expanduser("~"),
                ".dockify",
                "config.json"
            )
        else:
            self.config_path = config_path
            
        # Default configuration
        self.defaults = {
            "refresh_interval": 5,  # Data refresh interval in seconds
            "theme": "dark",        # UI theme (dark or light)
            "alert_thresholds": {
                "cpu_percent": 80.0,
                "memory_percent": 80.0
            },
            "container_alert_thresholds": {},  # Container-specific thresholds
            "window_size": {
                "width": 1200,
                "height": 800
            },
            "recent_containers": [],  # List of recently accessed containers
            "recent_reports": [],     # List of recently generated reports
            "reports_dir": os.path.join(os.path.expanduser("~"), "dockify_reports"),
            "show_notifications": True
        }
        
        # Current configuration (will be updated from file)
        self.config = self.defaults.copy()
        
        # Load configuration
        self.load()
        
    def load(self) -> bool:
        """
        Load configuration from file.
        
        Returns:
            True if configuration was loaded successfully, False otherwise
        """
        try:
            # Check if config file exists
            if not os.path.exists(self.config_path):
                # Create directory if it doesn't exist
                os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
                
                # Create default config file
                self.save()
                logger.info(f"Created default configuration at {self.config_path}")
                return True
                
            # Load configuration from file
            with open(self.config_path, 'r') as f:
                loaded_config = json.load(f)
                
            # Update configuration with loaded values
            for key, value in loaded_config.items():
                self.config[key] = value
                
            logger.info(f"Loaded configuration from {self.config_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            return False
            
    def save(self) -> bool:
        """
        Save configuration to file.
        
        Returns:
            True if configuration was saved successfully, False otherwise
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            
            # Save configuration to file
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
                
            logger.info(f"Saved configuration to {self.config_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
            return False
            
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.
        
        Args:
            key: Configuration key
            default: Default value to return if key is not found
            
        Returns:
            Configuration value or default
        """
        return self.config.get(key, default)
        
    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value.
        
        Args:
            key: Configuration key
            value: Configuration value
        """
        self.config[key] = value
        
    def get_alert_threshold(self, metric: str, container_id: Optional[str] = None) -> float:
        """
        Get alert threshold for a metric, optionally for a specific container.
        
        Args:
            metric: Metric name (e.g., 'cpu_percent', 'memory_percent')
            container_id: Container ID (optional)
            
        Returns:
            Threshold value
        """
        # Check for container-specific threshold
        if container_id is not None:
            container_thresholds = self.config.get('container_alert_thresholds', {})
            if container_id in container_thresholds and metric in container_thresholds[container_id]:
                return container_thresholds[container_id][metric]
                
        # Fall back to default threshold
        return self.config.get('alert_thresholds', {}).get(metric, self.defaults['alert_thresholds'].get(metric, 80.0))
        
    def set_alert_threshold(self, metric: str, value: float, container_id: Optional[str] = None) -> None:
        """
        Set alert threshold for a metric, optionally for a specific container.
        
        Args:
            metric: Metric name (e.g., 'cpu_percent', 'memory_percent')
            value: Threshold value
            container_id: Container ID (optional)
        """
        if container_id is not None:
            # Set container-specific threshold
            if 'container_alert_thresholds' not in self.config:
                self.config['container_alert_thresholds'] = {}
                
            if container_id not in self.config['container_alert_thresholds']:
                self.config['container_alert_thresholds'][container_id] = {}
                
            self.config['container_alert_thresholds'][container_id][metric] = value
        else:
            # Set default threshold
            if 'alert_thresholds' not in self.config:
                self.config['alert_thresholds'] = {}
                
            self.config['alert_thresholds'][metric] = value
            
    def add_recent_container(self, container_id: str, container_name: str) -> None:
        """
        Add a container to the recent containers list.
        
        Args:
            container_id: Container ID
            container_name: Container name
        """
        # Get recent containers list
        recent_containers = self.config.get('recent_containers', [])
        
        # Remove if already in list
        recent_containers = [c for c in recent_containers if c['id'] != container_id]
        
        # Add to beginning of list
        recent_containers.insert(0, {
            'id': container_id,
            'name': container_name
        })
        
        # Limit to 10 recent containers
        self.config['recent_containers'] = recent_containers[:10]
        
    def add_recent_report(self, report_path: str) -> None:
        """
        Add a report to the recent reports list.
        
        Args:
            report_path: Path to report file
        """
        # Get recent reports list
        recent_reports = self.config.get('recent_reports', [])
        
        # Remove if already in list
        recent_reports = [r for r in recent_reports if r != report_path]
        
        # Add to beginning of list
        recent_reports.insert(0, report_path)
        
        # Limit to 10 recent reports
        self.config['recent_reports'] = recent_reports[:10]
        
    def reset_to_defaults(self) -> None:
        """Reset configuration to default values."""
        self.config = self.defaults.copy()
