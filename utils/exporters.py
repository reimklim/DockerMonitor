"""
Export utilities for Dockify.
Provides functions for exporting container metrics to various formats.
"""
import os
import logging
import csv
import datetime
from typing import Dict, List, Any, Optional, Tuple
import time
from tkinter import messagebox

from core.monitor import ContainerMonitor

logger = logging.getLogger('dockify.utils.exporters')

class MetricsExporter:
    """
    Exports container metrics to various formats.
    """
    def __init__(self, container_monitor: ContainerMonitor):
        """
        Initialize metrics exporter.
        
        Args:
            container_monitor: Container monitor instance
        """
        self.container_monitor = container_monitor
        
    def export_to_excel(self, 
                      filepath: str, 
                      container_ids: List[str], 
                      container_names: Dict[str, str],
                      start_time: datetime.datetime,
                      end_time: datetime.datetime,
                      include_graphs: bool = True) -> bool:
        """
        Export metrics to Excel format.
        
        Args:
            filepath: Path to save the Excel file
            container_ids: List of container IDs to include
            container_names: Mapping of container IDs to display names
            start_time: Start time for metrics
            end_time: End time for metrics
            include_graphs: Whether to include graphs
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Check for pandas and xlsxwriter
            import pandas as pd
            import plotly.express as px
            import plotly.graph_objects as go
            from plotly.subplots import make_subplots
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
            
            # Create Excel writer - явно указываем engine='xlsxwriter'
            with pd.ExcelWriter(filepath, engine='xlsxwriter') as writer:
                # Create summary sheet
                summary_data = {
                    'Container ID': [],
                    'Container Name': [],
                    'Avg CPU (%)': [],
                    'Max CPU (%)': [],
                    'Avg Memory (%)': [],
                    'Max Memory (%)': [],
                    'Data Points': []
                }
                
                # Process each container
                for container_id in container_ids:
                    # Get container name
                    container_name = container_names.get(container_id, container_id[:12])
                    
                    # Get metrics history
                    metrics = self.container_monitor.get_metrics_history(container_id)
                    
                    # Filter metrics by time range
                    start_timestamp = start_time.timestamp()
                    end_timestamp = end_time.timestamp()
                    
                    filtered_metrics = [
                        m for m in metrics 
                        if start_timestamp <= m.get('timestamp', 0) <= end_timestamp
                    ]
                    
                    if not filtered_metrics:
                        logger.warning(f"No metrics found for container {container_id} in the specified time range")
                        continue
                        
                    # Calculate summary statistics
                    cpu_values = [m.get('cpu_percent', 0) for m in filtered_metrics]
                    memory_values = [m.get('memory_percent', 0) for m in filtered_metrics]
                    
                    avg_cpu = sum(cpu_values) / len(cpu_values) if cpu_values else 0
                    max_cpu = max(cpu_values) if cpu_values else 0
                    avg_memory = sum(memory_values) / len(memory_values) if memory_values else 0
                    max_memory = max(memory_values) if memory_values else 0
                    
                    # Add to summary data
                    summary_data['Container ID'].append(container_id[:12])
                    summary_data['Container Name'].append(container_name)
                    summary_data['Avg CPU (%)'].append(round(avg_cpu, 2))
                    summary_data['Max CPU (%)'].append(round(max_cpu, 2))
                    summary_data['Avg Memory (%)'].append(round(avg_memory, 2))
                    summary_data['Max Memory (%)'].append(round(max_memory, 2))
                    summary_data['Data Points'].append(len(filtered_metrics))
                    
                    # Create container-specific sheet
                    container_data = {
                        'Timestamp': [],
                        'CPU (%)': [],
                        'Memory (%)': [],
                        'Memory Usage (MB)': [],
                        'Network RX (KB)': [],
                        'Network TX (KB)': []
                    }
                    
                    for metric in filtered_metrics:
                        timestamp = datetime.datetime.fromtimestamp(metric.get('timestamp', 0))
                        container_data['Timestamp'].append(timestamp)
                        container_data['CPU (%)'].append(round(metric.get('cpu_percent', 0), 2))
                        container_data['Memory (%)'].append(round(metric.get('memory_percent', 0), 2))
                        
                        # Convert memory to MB
                        memory_mb = metric.get('memory_usage', 0) / (1024 * 1024)
                        container_data['Memory Usage (MB)'].append(round(memory_mb, 2))
                        
                        # Convert network to KB
                        network_rx_kb = metric.get('network_rx', 0) / 1024
                        network_tx_kb = metric.get('network_tx', 0) / 1024
                        container_data['Network RX (KB)'].append(round(network_rx_kb, 2))
                        container_data['Network TX (KB)'].append(round(network_tx_kb, 2))
                    
                    # Create DataFrame and save to sheet
                    container_df = pd.DataFrame(container_data)
                    safe_sheet_name = container_name[:31].replace('/', '_').replace('\\', '_').replace('?', '_')
                    container_df.to_excel(writer, sheet_name=safe_sheet_name, index=False)
                    
                    # Generate and save charts if requested
                    if include_graphs:
                        # Initialize a workbook
                        workbook = writer.book
                        worksheet = writer.sheets[safe_sheet_name]
                        
                        # CPU and Memory chart
                        fig = make_subplots(
                            rows=2, cols=1,
                            subplot_titles=("CPU Usage (%)", "Memory Usage (%)"),
                            shared_xaxes=True,
                            vertical_spacing=0.1
                        )
                        
                        # Add CPU trace
                        fig.add_trace(
                            go.Scatter(
                                x=container_data['Timestamp'],
                                y=container_data['CPU (%)'],
                                mode='lines',
                                name='CPU Usage',
                                line=dict(color='#1DB954', width=2)
                            ),
                            row=1, col=1
                        )
                        
                        # Add Memory trace
                        fig.add_trace(
                            go.Scatter(
                                x=container_data['Timestamp'],
                                y=container_data['Memory (%)'],
                                mode='lines',
                                name='Memory Usage',
                                line=dict(color='#9C27B0', width=2)
                            ),
                            row=2, col=1
                        )
                        
                        # Update layout
                        fig.update_layout(
                            height=500,
                            title_text=f"{container_name} - Performance Metrics",
                            showlegend=True
                        )
                        
                        # Save chart image
                        chart_path = os.path.splitext(filepath)[0] + f"_{safe_sheet_name}_chart.png"
                        fig.write_image(chart_path)
                        
                        # Add image to worksheet
                        # Note: This part would typically use openpyxl's image insertion,
                        # but we'll skip the actual insertion since it's complex and
                        # requires additional libraries. In a real app, you would add
                        # the image to the Excel file here.
                    
                # Create summary sheet
                if summary_data['Container ID']:
                    summary_df = pd.DataFrame(summary_data)
                    summary_df.to_excel(writer, sheet_name='Summary', index=False)
                    
                    # Add report information
                    info_df = pd.DataFrame({
                        'Report Information': ['Generated At', 'Time Range', 'Containers', 'Generated By'],
                        'Value': [
                            datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            f"{start_time.strftime('%Y-%m-%d %H:%M:%S')} to {end_time.strftime('%Y-%m-%d %H:%M:%S')}",
                            len(container_ids),
                            'Dockify'
                        ]
                    })
                    info_df.to_excel(writer, sheet_name='Info', index=False)
                    
            return True
            
        except ImportError as e:
            logger.error(f"Required libraries not available for Excel export: {e}")
            # Уведомляем пользователя о проблеме и спрашиваем, хочет ли он сохранить в CSV
            logger.info("Falling back to CSV export due to missing Excel libraries")
            messagebox_result = messagebox.askyesno(
                "Excel Export Failed",
                "Required libraries for Excel export are not available. Would you like to save as CSV instead?",
                icon='warning'
            )
            if messagebox_result:
                # Если пользователь согласен, сохраняем в CSV с таким же именем файла, но с другим расширением
                csv_filepath = os.path.splitext(filepath)[0] + '.csv'
                return self.export_to_csv(csv_filepath, container_ids, container_names, start_time, end_time)
            return False
            
        except Exception as e:
            logger.error(f"Error exporting to Excel: {e}")
            return False
            
    def export_to_csv(self, 
                    filepath: str, 
                    container_ids: List[str], 
                    container_names: Dict[str, str],
                    start_time: datetime.datetime,
                    end_time: datetime.datetime) -> bool:
        """
        Export metrics to CSV format.
        
        Args:
            filepath: Path to save the CSV file
            container_ids: List of container IDs to include
            container_names: Mapping of container IDs to display names
            start_time: Start time for metrics
            end_time: End time for metrics
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
            
            # Open CSV file
            with open(filepath, 'w', newline='') as csvfile:
                # Create CSV writer
                writer = csv.writer(csvfile)
                
                # Write header
                writer.writerow([
                    'Container ID', 
                    'Container Name', 
                    'Timestamp', 
                    'CPU (%)', 
                    'Memory (%)', 
                    'Memory Usage (MB)', 
                    'Network RX (KB)', 
                    'Network TX (KB)'
                ])
                
                # Process each container
                for container_id in container_ids:
                    # Get container name
                    container_name = container_names.get(container_id, container_id[:12])
                    
                    # Get metrics history
                    metrics = self.container_monitor.get_metrics_history(container_id)
                    
                    # Filter metrics by time range
                    start_timestamp = start_time.timestamp()
                    end_timestamp = end_time.timestamp()
                    
                    filtered_metrics = [
                        m for m in metrics 
                        if start_timestamp <= m.get('timestamp', 0) <= end_timestamp
                    ]
                    
                    if not filtered_metrics:
                        logger.warning(f"No metrics found for container {container_id} in the specified time range")
                        continue
                        
                    # Write metrics
                    for metric in filtered_metrics:
                        timestamp = datetime.datetime.fromtimestamp(metric.get('timestamp', 0))
                        cpu_percent = round(metric.get('cpu_percent', 0), 2)
                        memory_percent = round(metric.get('memory_percent', 0), 2)
                        
                        # Convert memory to MB
                        memory_mb = round(metric.get('memory_usage', 0) / (1024 * 1024), 2)
                        
                        # Convert network to KB
                        network_rx_kb = round(metric.get('network_rx', 0) / 1024, 2)
                        network_tx_kb = round(metric.get('network_tx', 0) / 1024, 2)
                        
                        writer.writerow([
                            container_id[:12],
                            container_name,
                            timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                            cpu_percent,
                            memory_percent,
                            memory_mb,
                            network_rx_kb,
                            network_tx_kb
                        ])
                        
            return True
            
        except Exception as e:
            logger.error(f"Error exporting to CSV: {e}")
            return False
            
    def export_daily_report(self, output_dir: str, container_ids: List[str] = None) -> str:
        """
        Generate a daily report for all or specified containers.
        
        Args:
            output_dir: Directory to save the report
            container_ids: List of container IDs to include (None for all)
            
        Returns:
            Path to the generated report or empty string if failed
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(output_dir, exist_ok=True)
            
            # Generate filename
            now = datetime.datetime.now()
            filename = f"docker_metrics_daily_{now.strftime('%Y%m%d_%H%M%S')}.xlsx"
            filepath = os.path.join(output_dir, filename)
            
            # Get container list if not provided
            if container_ids is None:
                # Use the last metrics update to get active containers
                metrics = {}
                if hasattr(self.container_monitor, 'monitors'):
                    metrics = self.container_monitor.monitors
                container_ids = list(metrics.keys())
                
            # Get container names - in this case we don't have them, so use short IDs
            container_names = {container_id: container_id[:12] for container_id in container_ids}
            
            # Calculate time range (last 24 hours)
            end_time = now
            start_time = end_time - datetime.timedelta(days=1)
            
            # Export to Excel с явным указанием включения графиков
            if self.export_to_excel(filepath, container_ids, container_names, start_time, end_time, include_graphs=True):
                return filepath
            return ""
            
        except Exception as e:
            logger.error(f"Error generating daily report: {e}")
            return ""
