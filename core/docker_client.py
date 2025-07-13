"""
Docker client wrapper for interacting with Docker API.
"""
import os
import logging
import json
from typing import Dict, List, Any, Optional, Union
import docker
from docker.errors import DockerException

logger = logging.getLogger('dockify.docker_client')

class DockerClient:
    """
    Wrapper around the Docker API client to provide simplified access to Docker resources.
    """
    def __init__(self, socket_path: str = '/var/run/docker.sock'):
        """
        Initialize the Docker client.
        
        Args:
            socket_path: Path to Docker socket (default: /var/run/docker.sock)
        """
        self.socket_path = socket_path
        self._initialize_client()
        
    def _initialize_client(self):
        """Initialize Docker client connection."""
        try:
            # Try different connection methods
            
            # Method 1: Standard connection from environment
            try:
                self.client = docker.from_env()
                self.api_client = self.client.api
                self.client.ping()
                logger.info("Docker client initialized successfully using from_env()")
                return
            except DockerException as e:
                logger.warning(f"Failed to initialize Docker client from environment: {e}")
            
            # Method 2: Try with direct socket connection
            try:
                # Use configured socket path
                if os.path.exists(self.socket_path):
                    self.client = docker.DockerClient(base_url=f'unix://{self.socket_path}')
                    self.api_client = self.client.api
                    self.client.ping()
                    logger.info(f"Docker client initialized successfully using unix socket: {self.socket_path}")
                    return
            except DockerException as e:
                logger.warning(f"Failed to initialize Docker client with unix socket: {e}")
            
            # Method 3: Try with TCP connection
            try:
                self.client = docker.DockerClient(base_url='tcp://localhost:2375')
                self.api_client = self.client.api
                self.client.ping()
                logger.info("Docker client initialized successfully using TCP connection")
                return
            except DockerException as e:
                logger.warning(f"Failed to initialize Docker client with TCP connection: {e}")
                
            # If we reach here, all connection attempts failed
            raise DockerException("Could not connect to Docker daemon. Make sure Docker is running.")
            
        except DockerException as e:
            logger.error(f"Failed to initialize Docker client: {e}")
            raise
            
    @property
    def socket_path(self) -> str:
        """Get the Docker socket path."""
        return self._socket_path
        
    @socket_path.setter
    def socket_path(self, path: str):
        """
        Set the Docker socket path and reinitialize the client.
        
        Args:
            path: Path to Docker socket
        """
        self._socket_path = path
        # Если клиент уже был инициализирован, переинициализируем его
        if hasattr(self, 'client'):
            logger.info(f"Updating Docker socket path to {path}")
            self._initialize_client()

    def list_containers(self, all_containers: bool = True) -> List[Dict[str, Any]]:
        """
        List all containers.
        
        Args:
            all_containers: Whether to include stopped containers
            
        Returns:
            List of container dictionaries
        """
        try:
            containers = self.client.containers.list(all=all_containers)
            # Convert Container objects to dictionaries with necessary attributes
            container_dicts = []
            for container in containers:
                # Build a dictionary with the required attributes
                container_dict = {
                    'Id': container.id,
                    'Names': [container.name],
                    'Image': container.image.tags[0] if container.image.tags else container.image.id,
                    'ImageID': container.image.id,
                    'State': container.status,
                    'Status': container.status,
                    'Created': container.attrs.get('Created', ''),
                    'Ports': self._extract_ports(container),
                    'Labels': container.labels,
                    'Command': container.attrs.get('Config', {}).get('Cmd', [])
                }
                container_dicts.append(container_dict)
            return container_dicts
        except DockerException as e:
            logger.error(f"Failed to list containers: {e}")
            return []
            
    def _extract_ports(self, container) -> List[Dict[str, Any]]:
        """Extract port information from container attributes."""
        try:
            ports = []
            port_bindings = container.attrs.get('HostConfig', {}).get('PortBindings', {})
            for container_port, bindings in port_bindings.items():
                if bindings:
                    for binding in bindings:
                        port_info = {
                            'IP': binding.get('HostIp', '0.0.0.0'),
                            'PrivatePort': container_port.split('/')[0],
                            'PublicPort': binding.get('HostPort', ''),
                            'Type': container_port.split('/')[1] if '/' in container_port else 'tcp'
                        }
                        ports.append(port_info)
            return ports
        except Exception as e:
            logger.error(f"Failed to extract port information: {e}")
            return []

    def get_container(self, container_id: str) -> Optional[Dict[str, Any]]:
        """
        Get details for a specific container.
        
        Args:
            container_id: Container ID or name
            
        Returns:
            Container details or None if not found
        """
        try:
            container = self.client.containers.get(container_id)
            # Get detailed container info with inspection
            return self.api_client.inspect_container(container.id)
        except DockerException as e:
            logger.error(f"Failed to get container {container_id}: {e}")
            return None

    def start_container(self, container_id: str) -> bool:
        """
        Start a container.
        
        Args:
            container_id: Container ID or name
            
        Returns:
            True if successful, False otherwise
        """
        try:
            container = self.client.containers.get(container_id)
            container.start()
            logger.info(f"Container {container_id} started")
            return True
        except DockerException as e:
            logger.error(f"Failed to start container {container_id}: {e}")
            return False

    def stop_container(self, container_id: str) -> bool:
        """
        Stop a container.
        
        Args:
            container_id: Container ID or name
            
        Returns:
            True if successful, False otherwise
        """
        try:
            container = self.client.containers.get(container_id)
            container.stop()
            logger.info(f"Container {container_id} stopped")
            return True
        except DockerException as e:
            logger.error(f"Failed to stop container {container_id}: {e}")
            return False

    def restart_container(self, container_id: str) -> bool:
        """
        Restart a container.
        
        Args:
            container_id: Container ID or name
            
        Returns:
            True if successful, False otherwise
        """
        try:
            container = self.client.containers.get(container_id)
            container.restart()
            logger.info(f"Container {container_id} restarted")
            return True
        except DockerException as e:
            logger.error(f"Failed to restart container {container_id}: {e}")
            return False

    def remove_container(self, container_id: str, force: bool = False) -> bool:
        """
        Remove a container.
        
        Args:
            container_id: Container ID or name
            force: Whether to force removal of a running container
            
        Returns:
            True if successful, False otherwise
        """
        try:
            container = self.client.containers.get(container_id)
            container.remove(force=force)
            logger.info(f"Container {container_id} removed")
            return True
        except DockerException as e:
            logger.error(f"Failed to remove container {container_id}: {e}")
            return False

    def get_container_stats(self, container_id: str) -> Dict[str, Any]:
        """
        Get real-time stats for a container.
        
        Args:
            container_id: Container ID or name
            
        Returns:
            Dictionary with container stats
        """
        try:
            import time
            start_time = time.time()
            
            # Используем низкоуровневый API для более быстрого получения статистики
            # stream=False означает, что мы получаем только один снимок статистики
            stats_obj = self.api_client.stats(container=container_id, stream=False)
            
            # Если мы получили пустой объект, вернем пустые метрики
            if not stats_obj:
                logger.warning(f"No stats received for container {container_id}")
                return {
                    'cpu_percent': 0.0,
                    'memory_usage': 0,
                    'memory_limit': 0,
                    'memory_percent': 0.0,
                    'network_rx': 0,
                    'network_tx': 0
                }
            
            # Process CPU stats - handle potential missing keys
            cpu_percent = 0.0
            try:
                # Некоторые версии Docker могут не иметь всех этих метрик
                cpu_delta = stats_obj.get('cpu_stats', {}).get('cpu_usage', {}).get('total_usage', 0) - \
                            stats_obj.get('precpu_stats', {}).get('cpu_usage', {}).get('total_usage', 0)
                
                # Проверяем наличие system_cpu_usage - это частый источник ошибок
                system_cpu_usage = stats_obj.get('cpu_stats', {}).get('system_cpu_usage', 0)
                pre_system_cpu_usage = stats_obj.get('precpu_stats', {}).get('system_cpu_usage', 0)
                
                if system_cpu_usage and pre_system_cpu_usage:
                    system_delta = system_cpu_usage - pre_system_cpu_usage
                    
                    # Получаем количество ядер CPU
                    online_cpus = stats_obj.get('cpu_stats', {}).get('online_cpus', 0)
                    if not online_cpus and 'cpu_usage' in stats_obj.get('cpu_stats', {}) and 'percpu_usage' in stats_obj['cpu_stats']['cpu_usage']:
                        online_cpus = len(stats_obj['cpu_stats']['cpu_usage']['percpu_usage'])
                    if not online_cpus:
                        online_cpus = 1  # Если не удалось определить, используем 1 ядро
                    
                    # Вычисляем процент использования CPU
                    if system_delta > 0 and cpu_delta > 0:
                        cpu_percent = (cpu_delta / system_delta) * online_cpus * 100.0
            except Exception as e:
                logger.warning(f"Error calculating CPU usage: {e}")
                
            # Process memory stats
            memory_usage = 0
            memory_limit = 0 
            memory_percent = 0.0
            
            try:
                memory_stats = stats_obj.get('memory_stats', {})
                if memory_stats:
                    memory_usage = memory_stats.get('usage', 0)
                    memory_limit = memory_stats.get('limit', 1)  # Избегаем деления на ноль
                    
                    if memory_limit > 0:  # Проверка для избежания деления на ноль
                        memory_percent = (memory_usage / memory_limit) * 100.0
            except Exception as e:
                logger.warning(f"Error calculating memory usage: {e}")
            
            # Process network stats if available
            network_rx = 0
            network_tx = 0
            try:
                networks = stats_obj.get('networks', {})
                if networks:
                    for interface, net_stats in networks.items():
                        network_rx += net_stats.get('rx_bytes', 0)
                        network_tx += net_stats.get('tx_bytes', 0)
            except Exception as e:
                logger.warning(f"Error calculating network usage: {e}")
            
            end_time = time.time()
            if end_time - start_time > 0.5:  # Логируем только медленные запросы
                logger.debug(f"Docker stats API call for container {container_id} took {end_time - start_time:.3f} seconds")
            
            return {
                'cpu_percent': cpu_percent,
                'memory_usage': memory_usage,
                'memory_limit': memory_limit,
                'memory_percent': memory_percent,
                'network_rx': network_rx,
                'network_tx': network_tx
            }
        except Exception as e:
            logger.error(f"Failed to get stats for container {container_id}: {e}")
            return {
                'cpu_percent': 0.0,
                'memory_usage': 0,
                'memory_limit': 0,
                'memory_percent': 0.0,
                'network_rx': 0,
                'network_tx': 0
            }

    def list_images(self) -> List[Dict[str, Any]]:
        """
        List all images.
        
        Returns:
            List of image dictionaries
        """
        try:
            images = self.client.images.list()
            # Convert Image objects to dictionaries
            image_dicts = []
            for image in images:
                image_dict = {
                    'Id': image.id,
                    'RepoTags': image.tags if image.tags else ['<none>:<none>'],
                    'Size': image.attrs.get('Size', 0),
                    'Created': image.attrs.get('Created', ''),
                    'Labels': image.labels or {}
                }
                image_dicts.append(image_dict)
            return image_dicts
        except DockerException as e:
            logger.error(f"Failed to list images: {e}")
            return []

    def get_container_logs(self, container_id: str, tail: int = 100) -> str:
        """
        Get container logs.
        
        Args:
            container_id: Container ID or name
            tail: Number of lines to tail from the end of the logs
            
        Returns:
            Container logs as a string
        """
        try:
            container = self.client.containers.get(container_id)
            logs = container.logs(tail=tail, timestamps=True, stream=False)
            if isinstance(logs, bytes):
                return logs.decode('utf-8', errors='replace')
            return str(logs)
        except DockerException as e:
            logger.error(f"Failed to get logs for container {container_id}: {e}")
            return f"Error retrieving logs: {e}"

    def get_container_file_tree(self, container_id: str, path: str = '/') -> List[Dict[str, Any]]:
        """
        Get container file tree (directory listing).
        
        Args:
            container_id: Container ID or name
            path: Path inside the container
            
        Returns:
            List of file dictionaries
        """
        try:
            container = self.client.containers.get(container_id)
            exec_result = container.exec_run(f"ls -la {path}")
            
            if exec_result.exit_code != 0:
                logger.error(f"Failed to get file tree for container {container_id}: {exec_result.output}")
                return []
                
            output = exec_result.output.decode('utf-8', errors='replace')
            files = []
            
            # Parse ls -la output
            for line in output.splitlines()[1:]:  # Skip total line
                parts = line.split()
                if len(parts) >= 9:
                    file_type = 'directory' if parts[0].startswith('d') else 'file'
                    name = ' '.join(parts[8:])
                    files.append({
                        'name': name,
                        'type': file_type,
                        'size': parts[4],
                        'permissions': parts[0],
                        'path': f"{path.rstrip('/')}/{name}"
                    })
                    
            return files
        except DockerException as e:
            logger.error(f"Failed to get file tree for container {container_id}: {e}")
            return []

    def read_container_file(self, container_id: str, file_path: str) -> str:
        """
        Read file content from a container.
        
        Args:
            container_id: Container ID or name
            file_path: Path to the file inside the container
            
        Returns:
            File content as a string or error message
        """
        try:
            container = self.client.containers.get(container_id)
            # Use cat to get file content
            exec_result = container.exec_run(f"cat {file_path}")
            
            if exec_result.exit_code != 0:
                logger.error(f"Failed to read file {file_path} from container {container_id}: {exec_result.output}")
                return f"Error reading file: {exec_result.output.decode('utf-8', errors='replace')}"
                
            return exec_result.output.decode('utf-8', errors='replace')
        except DockerException as e:
            logger.error(f"Failed to read file {file_path} from container {container_id}: {e}")
            return f"Error reading file: {e}"

    def get_docker_info(self) -> Dict[str, Any]:
        """
        Get Docker system information.
        
        Returns:
            Dictionary with Docker system info
        """
        try:
            return self.client.info()
        except DockerException as e:
            logger.error(f"Failed to get Docker info: {e}")
            return {}
