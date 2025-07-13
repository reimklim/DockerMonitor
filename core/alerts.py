"""
Alerts management and threshold checking functionality for Docker containers.
"""
import logging
import time
from typing import Dict, List, Any, Optional, Callable, Set, Tuple

logger = logging.getLogger('dockify.alerts')

class AlertManager:
    """
    Manager for container metric alerts based on configurable thresholds.
    """
    def __init__(self):
        """Initialize the alert manager."""
        # Default thresholds
        self.default_thresholds = {
            'cpu_percent': 80.0,
            'memory_percent': 80.0
        }
        
        # Container-specific thresholds
        self.container_thresholds: Dict[str, Dict[str, float]] = {}
        
        # Active alerts
        self.active_alerts: Dict[str, Dict[str, Any]] = {}
        
        # Alert history
        self.alert_history: List[Dict[str, Any]] = []
        
        # Callback functions
        self.callbacks: List[Callable] = []
        
    def set_default_threshold(self, metric: str, value: float) -> None:
        """
        Set a default threshold for a specific metric.
        
        Args:
            metric: Metric name (e.g., 'cpu_percent', 'memory_percent')
            value: Threshold value
        """
        self.default_thresholds[metric] = value
        logger.info(f"Default threshold for {metric} set to {value}")
        
    def set_container_threshold(self, container_id: str, metric: str, value: float) -> None:
        """
        Set a container-specific threshold.
        
        Args:
            container_id: Container ID
            metric: Metric name
            value: Threshold value
        """
        if container_id not in self.container_thresholds:
            self.container_thresholds[container_id] = {}
            
        self.container_thresholds[container_id][metric] = value
        logger.info(f"Threshold for container {container_id}, metric {metric} set to {value}")
        
    def get_threshold(self, container_id: str, metric: str) -> float:
        """
        Get the threshold for a specific container and metric.
        
        Args:
            container_id: Container ID
            metric: Metric name
            
        Returns:
            Threshold value
        """
        # Check for container-specific threshold
        if container_id in self.container_thresholds and metric in self.container_thresholds[container_id]:
            return self.container_thresholds[container_id][metric]
            
        # Fall back to default threshold
        return self.default_thresholds.get(metric, float('inf'))
        
    def check_alerts(self, metrics: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Check metrics against thresholds and generate alerts.
    
        Args:
            metrics: Dictionary of container metrics, keyed by container ID
    
        Returns:
            List of new alerts
        """
        new_alerts: List[Dict[str, Any]] = []
        checked_alerts: Set[Tuple[str, str]] = set()
    
        # Check each container's metrics against thresholds
        for container_id, container_metrics in metrics.items():
            for metric in ['cpu_percent', 'memory_percent']:
                if metric in container_metrics:
                    threshold = self.get_threshold(container_id, metric)
                    value = container_metrics[metric]
                    alert_key = (container_id, metric)
                    checked_alerts.add(alert_key)
    
                    # Check if value exceeds threshold
                    if value > threshold:
                        # Create or update alert
                        alert_id = f"{container_id}_{metric}"
                        if alert_id not in self.active_alerts:
                            # New alert
                            alert = {
                                'id': alert_id,
                                'container_id': container_id,
                                'container_name': container_metrics.get('name', 'unknown'),
                                'metric': metric,
                                'threshold': threshold,
                                'value': value,
                                'start_time': time.time(),
                                'last_updated': time.time(),
                                'status': 'active'
                            }
                            self.active_alerts[alert_id] = alert
                            new_alerts.append(alert)
                            self.alert_history.append(alert.copy())
                            logger.warning(f"New alert: {container_metrics.get('name', 'unknown')} - {metric} {value:.1f}% > {threshold:.1f}%")
                        else:
                            # Update existing alert
                            self.active_alerts[alert_id]['value'] = value
                            self.active_alerts[alert_id]['last_updated'] = time.time()
    
                    # Value back to normal — resolve alert
                    else:
                        alert_id = f"{container_id}_{metric}"
                        if alert_id in self.active_alerts:
                            self.active_alerts[alert_id]['status'] = 'resolved'
                            self.active_alerts[alert_id]['resolve_time'] = time.time()
                            self.alert_history.append(self.active_alerts[alert_id].copy())
                            del self.active_alerts[alert_id]
                            logger.info(f"Alert resolved: {container_metrics.get('name', 'unknown')} - {metric}")
    
        # Handle containers that no longer exist or aren't reporting metrics
        to_resolve = []
        for alert_id, alert in self.active_alerts.items():
            container_id = alert['container_id']
            metric = alert['metric']
    
            if (container_id, metric) not in checked_alerts:
                alert['status'] = 'resolved'
                alert['resolve_time'] = time.time()
                self.alert_history.append(alert.copy())
                to_resolve.append(alert_id)
                logger.info(f"Alert auto-resolved: {alert['container_name']} - {metric}")
    
        # Clean up resolved alerts
        for alert_id in to_resolve:
            del self.active_alerts[alert_id]
    
        # Notify callbacks if there are new alerts
        if new_alerts and self.callbacks:
            for callback in self.callbacks:
                try:
                    callback(new_alerts)
                except Exception as e:
                    logger.error(f"Error in alert callback: {e}")
    
        return new_alerts
        
    def add_callback(self, callback: Callable) -> None:
        """
        Add a callback function that will be called when new alerts are generated.
        
        Args:
            callback: Function to call with new alerts
        """
        if callback not in self.callbacks:
            self.callbacks.append(callback)
            
    def remove_callback(self, callback: Callable) -> None:
        """
        Remove a callback function.
        
        Args:
            callback: Function to remove from callbacks
        """
        if callback in self.callbacks:
            self.callbacks.remove(callback)
            
    def get_active_alerts(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all active alerts.
        
        Returns:
            Dictionary of active alerts
        """
        return self.active_alerts
        
    def get_alert_history(self) -> List[Dict[str, Any]]:
        """
        Get alert history.
        
        Returns:
            List of historical alerts
        """
        return self.alert_history
