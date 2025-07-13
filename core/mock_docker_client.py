"""
Mock Docker client for demo mode.
Provides simulated Docker data for when a real Docker connection is not available.
"""
import os
import time
import math
import logging
import random
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger('dockify.mock_docker_client')

class MockDockerClient:
    """
    Mock Docker client that provides simulated data for demo mode.
    """
    def __init__(self):
        """Initialize the mock Docker client."""
        logger.info("Initializing mock Docker client for demo mode")
        self.api_client = self  # For API compatibility
        
        # Create mock containers
        self.mock_containers = [
            {
                'Id': 'c1234567890abcdef',
                'Names': ['/web-server'],
                'Image': 'nginx:latest',
                'ImageID': 'sha256:1234567890abcdef',
                'Command': 'nginx -g daemon off;',
                'Created': int(time.time()) - 86400,
                'State': 'running',
                'Status': 'Up 24 hours',
                'Ports': [{'IP': '0.0.0.0', 'PrivatePort': 80, 'PublicPort': 8080, 'Type': 'tcp'}],
                'Labels': {},
                'NetworkSettings': {
                    'Networks': {
                        'bridge': {
                            'IPAddress': '172.17.0.2',
                            'Gateway': '172.17.0.1'
                        }
                    }
                }
            },
            {
                'Id': 'c2345678901abcdef',
                'Names': ['/database'],
                'Image': 'postgres:14',
                'ImageID': 'sha256:2345678901abcdef',
                'Command': 'postgres',
                'Created': int(time.time()) - 172800,
                'State': 'running',
                'Status': 'Up 2 days',
                'Ports': [{'IP': '0.0.0.0', 'PrivatePort': 5432, 'PublicPort': 5432, 'Type': 'tcp'}],
                'Labels': {},
                'NetworkSettings': {
                    'Networks': {
                        'bridge': {
                            'IPAddress': '172.17.0.3',
                            'Gateway': '172.17.0.1'
                        }
                    }
                }
            },
            {
                'Id': 'c3456789012abcdef',
                'Names': ['/backend-api'],
                'Image': 'nodejs:16',
                'ImageID': 'sha256:3456789012abcdef',
                'Command': 'node server.js',
                'Created': int(time.time()) - 43200,
                'State': 'running',
                'Status': 'Up 12 hours',
                'Ports': [{'IP': '0.0.0.0', 'PrivatePort': 3000, 'PublicPort': 3000, 'Type': 'tcp'}],
                'Labels': {},
                'NetworkSettings': {
                    'Networks': {
                        'bridge': {
                            'IPAddress': '172.17.0.4',
                            'Gateway': '172.17.0.1'
                        }
                    }
                }
            },
            {
                'Id': 'c4567890123abcdef',
                'Names': ['/redis-cache'],
                'Image': 'redis:alpine',
                'ImageID': 'sha256:4567890123abcdef',
                'Command': 'redis-server',
                'Created': int(time.time()) - 129600,
                'State': 'running',
                'Status': 'Up 36 hours',
                'Ports': [{'IP': '0.0.0.0', 'PrivatePort': 6379, 'PublicPort': 6379, 'Type': 'tcp'}],
                'Labels': {},
                'NetworkSettings': {
                    'Networks': {
                        'bridge': {
                            'IPAddress': '172.17.0.5',
                            'Gateway': '172.17.0.1'
                        }
                    }
                }
            },
            {
                'Id': 'c5678901234abcdef',
                'Names': ['/backup-service'],
                'Image': 'alpine:latest',
                'ImageID': 'sha256:5678901234abcdef',
                'Command': '/bin/sh -c while true; do sleep 3600; done',
                'Created': int(time.time()) - 259200,
                'State': 'exited',
                'Status': 'Exited (0) 2 hours ago',
                'Ports': [],
                'Labels': {},
                'NetworkSettings': {
                    'Networks': {
                        'bridge': {
                            'IPAddress': '',
                            'Gateway': ''
                        }
                    }
                }
            }
        ]
        
        # Mock images
        self.mock_images = [
            {
                'Id': 'sha256:1234567890abcdef',
                'RepoTags': ['nginx:latest'],
                'Created': int(time.time()) - 2592000,
                'Size': 142000000
            },
            {
                'Id': 'sha256:2345678901abcdef',
                'RepoTags': ['postgres:14'],
                'Created': int(time.time()) - 5184000,
                'Size': 314000000
            },
            {
                'Id': 'sha256:3456789012abcdef',
                'RepoTags': ['nodejs:16'],
                'Created': int(time.time()) - 3456000,
                'Size': 187000000
            },
            {
                'Id': 'sha256:4567890123abcdef',
                'RepoTags': ['redis:alpine'],
                'Created': int(time.time()) - 6048000,
                'Size': 32000000
            },
            {
                'Id': 'sha256:5678901234abcdef',
                'RepoTags': ['alpine:latest'],
                'Created': int(time.time()) - 8640000,
                'Size': 5000000
            }
        ]
        
        # Mock files in containers
        self.mock_files = {
            'c1234567890abcdef': {
                '/': [
                    {'name': 'etc', 'type': 'directory', 'size': '4096', 'permissions': 'drwxr-xr-x', 'path': '/etc'},
                    {'name': 'var', 'type': 'directory', 'size': '4096', 'permissions': 'drwxr-xr-x', 'path': '/var'},
                    {'name': 'usr', 'type': 'directory', 'size': '4096', 'permissions': 'drwxr-xr-x', 'path': '/usr'}
                ],
                '/etc': [
                    {'name': 'nginx', 'type': 'directory', 'size': '4096', 'permissions': 'drwxr-xr-x', 'path': '/etc/nginx'},
                    {'name': 'passwd', 'type': 'file', 'size': '589', 'permissions': '-rw-r--r--', 'path': '/etc/passwd'},
                    {'name': 'hosts', 'type': 'file', 'size': '178', 'permissions': '-rw-r--r--', 'path': '/etc/hosts'}
                ],
                '/etc/nginx': [
                    {'name': 'nginx.conf', 'type': 'file', 'size': '756', 'permissions': '-rw-r--r--', 'path': '/etc/nginx/nginx.conf'},
                    {'name': 'conf.d', 'type': 'directory', 'size': '4096', 'permissions': 'drwxr-xr-x', 'path': '/etc/nginx/conf.d'}
                ]
            }
        }
        
        # Mock file contents
        self.mock_file_contents = {
            'c1234567890abcdef': {
                '/etc/nginx/nginx.conf': """
user  nginx;
worker_processes  auto;

error_log  /var/log/nginx/error.log notice;
pid        /var/run/nginx.pid;

events {
    worker_connections  1024;
}

http {
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;

    log_format  main  '$remote_addr - $remote_user [$time_local] "$request" '
                      '$status $body_bytes_sent "$http_referer" '
                      '"$http_user_agent" "$http_x_forwarded_for"';

    access_log  /var/log/nginx/access.log  main;

    sendfile        on;
    keepalive_timeout  65;
    
    include /etc/nginx/conf.d/*.conf;
}
                """,
                '/etc/hosts': """
127.0.0.1       localhost
::1     localhost ip6-localhost ip6-loopback
fe00::0 ip6-localnet
ff00::0 ip6-mcastprefix
ff02::1 ip6-allnodes
ff02::2 ip6-allrouters
172.17.0.2      c1234567890a
                """
            }
        }
        
        # Metrics data for simulating container stats
        self.init_time = time.time()
        self.base_metrics = {
            'c1234567890abcdef': {
                'cpu_baseline': 15.0,
                'memory_usage': 1_000_000_000,
                'memory_limit': 8_000_000_000,
                'network_rx_rate': 1000,
                'network_tx_rate': 2000
            },
            'c2345678901abcdef': {
                'cpu_baseline': 30.0,
                'memory_usage': 2_500_000_000,
                'memory_limit': 8_000_000_000,
                'network_rx_rate': 500,
                'network_tx_rate': 800
            },
            'c3456789012abcdef': {
                'cpu_baseline': 20.0,
                'memory_usage': 800_000_000,
                'memory_limit': 8_000_000_000,
                'network_rx_rate': 1500,
                'network_tx_rate': 1200
            },
            'c4567890123abcdef': {
                'cpu_baseline': 5.0,
                'memory_usage': 300_000_000,
                'memory_limit': 8_000_000_000,
                'network_rx_rate': 200,
                'network_tx_rate': 150
            }
        }
        
        # Last metrics update
        self.last_update = time.time()
        self.total_rx = {c_id: 0 for c_id in self.base_metrics}
        self.total_tx = {c_id: 0 for c_id in self.base_metrics}
    
    def ping(self):
        """Simulated ping for connection checking."""
        return True
        
    def get_docker_info(self) -> Dict[str, Any]:
        """
        Get general Docker info for the system.
        
        Returns:
            Dictionary with system and Docker info
        """
        return {
            "ID": "MOCK_DOCKER_ID",
            "Containers": len(self.mock_containers),
            "ContainersRunning": len([c for c in self.mock_containers if c["State"] == "running"]),
            "ContainersPaused": 0,
            "ContainersStopped": len([c for c in self.mock_containers if c["State"] == "exited"]),
            "Images": len(self.mock_images),
            "Driver": "overlay2",
            "DriverStatus": [["Backing Filesystem", "extfs"]],
            "SystemStatus": None,
            "Plugins": {
                "Volume": ["local"],
                "Network": ["bridge", "host", "ipvlan", "macvlan", "null", "overlay"],
                "Authorization": None,
                "Log": ["awslogs", "fluentd", "gcplogs", "gelf", "journald", "json-file", "local", "logentries", "splunk", "syslog"]
            },
            "MemTotal": 16800000000,
            "MemFree": 8400000000,
            "SwapLimit": True,
            "KernelVersion": "5.15.0-25-generic",
            "OperatingSystem": "Ubuntu 22.04 LTS (Demo)",
            "OSType": "linux",
            "Architecture": "x86_64",
            "NCPU": 8,
            "DockerRootDir": "/var/lib/docker",
            "HttpProxy": "",
            "HttpsProxy": "",
            "NoProxy": "",
            "ServerVersion": "24.0.5",
            "Swarm": {
                "NodeID": "",
                "NodeAddr": "",
                "LocalNodeState": "inactive"
            }
        }
        
    def list_containers(self, all_containers: bool = True) -> List[Dict[str, Any]]:
        """
        List all mock containers.
        
        Args:
            all_containers: Whether to include stopped containers
            
        Returns:
            List of container dictionaries
        """
        if all_containers:
            return self.mock_containers
        else:
            return [c for c in self.mock_containers if c['State'] == 'running']
            
    def containers(self):
        """
        Docker-py API compatibility for containers.
        """
        class MockContainerCollection:
            def list(self, all=True, sparse=True):
                return self.parent.list_containers(all)
                
            def get(self, container_id):
                return MockContainer(self.parent, container_id)
                
            def __init__(self, parent):
                self.parent = parent
                
        return MockContainerCollection(self)
    
    def images(self):
        """
        Docker-py API compatibility for images.
        """
        class MockImageCollection:
            def list(self):
                return self.parent.mock_images
                
            def __init__(self, parent):
                self.parent = parent
                
        return MockImageCollection(self)
        
    def get_container(self, container_id: str) -> Optional[Dict[str, Any]]:
        """
        Get details for a specific mock container.
        
        Args:
            container_id: Container ID or name
            
        Returns:
            Container details or None if not found
        """
        # Handle name format
        if container_id.startswith('/'):
            for container in self.mock_containers:
                if container_id in container['Names']:
                    return container
        else:
            for container in self.mock_containers:
                if container['Id'] == container_id or container['Id'].startswith(container_id):
                    return container
        return None
        
    def inspect_container(self, container_id: str) -> Dict[str, Any]:
        """
        Get detailed container info.
        
        Args:
            container_id: Container ID
            
        Returns:
            Container inspection details
        """
        container = self.get_container(container_id)
        if not container:
            return {}
            
        # Create inspection result with more details
        inspection = {
            'Id': container['Id'],
            'Name': container['Names'][0],
            'Config': {
                'Image': container['Image'],
                'Cmd': container['Command'].split(),
                'Hostname': container['Id'][:12],
                'ExposedPorts': {},
                'Env': ['PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin']
            },
            'State': {
                'Status': container['State'],
                'Running': container['State'] == 'running',
                'Paused': False,
                'Restarting': False,
                'Dead': False,
                'Pid': 2345 if container['State'] == 'running' else 0,
                'StartedAt': datetime.now().isoformat() if container['State'] == 'running' else '',
                'FinishedAt': '' if container['State'] == 'running' else datetime.now().isoformat()
            },
            'NetworkSettings': container['NetworkSettings'],
            'Mounts': [
                {
                    'Source': '/host/path',
                    'Destination': '/container/path',
                    'Mode': 'rw',
                    'RW': True
                }
            ]
        }
        
        # Add exposed ports
        for port in container.get('Ports', []):
            if 'PublicPort' in port:
                key = f"{port['PrivatePort']}/{port['Type']}"
                inspection['Config']['ExposedPorts'][key] = {}
                
        return inspection
        
    def start_container(self, container_id: str) -> bool:
        """
        Start a mock container.
        
        Args:
            container_id: Container ID or name
            
        Returns:
            True if successful, False otherwise
        """
        container = self.get_container(container_id)
        if container and container['State'] != 'running':
            container['State'] = 'running'
            container['Status'] = 'Up 0 seconds'
            return True
        return False
        
    def stop_container(self, container_id: str) -> bool:
        """
        Stop a mock container.
        
        Args:
            container_id: Container ID or name
            
        Returns:
            True if successful, False otherwise
        """
        container = self.get_container(container_id)
        if container and container['State'] == 'running':
            container['State'] = 'exited'
            container['Status'] = 'Exited (0) 0 seconds ago'
            return True
        return False
        
    def restart_container(self, container_id: str) -> bool:
        """
        Restart a mock container.
        
        Args:
            container_id: Container ID or name
            
        Returns:
            True if successful, False otherwise
        """
        container = self.get_container(container_id)
        if container:
            container['State'] = 'running'
            container['Status'] = 'Up 0 seconds'
            return True
        return False
        
    def remove_container(self, container_id: str, force: bool = False) -> bool:
        """
        Remove a mock container.
        
        Args:
            container_id: Container ID or name
            force: Whether to force removal of a running container
            
        Returns:
            True if successful, False otherwise
        """
        for i, container in enumerate(self.mock_containers):
            if container['Id'] == container_id or container['Id'].startswith(container_id):
                if container['State'] == 'running' and not force:
                    return False
                self.mock_containers.pop(i)
                return True
        return False
        
    def get_container_stats(self, container_id: str) -> Dict[str, Any]:
        """
        Get simulated stats for a container.
        
        Args:
            container_id: Container ID or name
            
        Returns:
            Dictionary with container stats
        """
        container = self.get_container(container_id)
        if not container or container['State'] != 'running':
            return {
                'cpu_percent': 0.0,
                'memory_usage': 0,
                'memory_limit': 0,
                'memory_percent': 0.0,
                'network_rx': 0,
                'network_tx': 0
            }
            
        # Get base metrics
        base = self.base_metrics.get(container['Id'], {
            'cpu_baseline': 10.0,
            'memory_usage': 500_000_000,
            'memory_limit': 8_000_000_000,
            'network_rx_rate': 1000,
            'network_tx_rate': 1000
        })
        
        # Calculate time delta since last update
        now = time.time()
        time_delta = now - self.last_update
        self.last_update = now
        
        # Simulate fluctuations
        elapsed_time = now - self.init_time
        cpu_percent = base['cpu_baseline'] + 5.0 * math.sin(elapsed_time / 30)
        cpu_percent += random.uniform(-3.0, 3.0)
        cpu_percent = max(0.1, min(99.9, cpu_percent))
        
        memory_usage = base['memory_usage'] + int(base['memory_usage'] * 0.1 * math.sin(elapsed_time / 60))
        memory_usage += random.randint(-50_000_000, 50_000_000)
        memory_usage = max(1_000_000, min(base['memory_limit'] - 1_000_000, memory_usage))
        
        memory_percent = (memory_usage / base['memory_limit']) * 100.0
        
        # Network traffic simulation
        self.total_rx[container['Id']] += int(base['network_rx_rate'] * time_delta) + random.randint(0, 1000)
        self.total_tx[container['Id']] += int(base['network_tx_rate'] * time_delta) + random.randint(0, 1000)
        
        return {
            'cpu_percent': cpu_percent,
            'memory_usage': memory_usage,
            'memory_limit': base['memory_limit'],
            'memory_percent': memory_percent,
            'network_rx': self.total_rx[container['Id']],
            'network_tx': self.total_tx[container['Id']]
        }
        
    def list_images(self) -> List[Dict[str, Any]]:
        """
        List all mock images.
        
        Returns:
            List of image dictionaries
        """
        return self.mock_images
        
    def get_container_logs(self, container_id: str, tail: int = 100) -> str:
        """
        Get simulated logs for a container.
        
        Args:
            container_id: Container ID or name
            tail: Number of lines to return
            
        Returns:
            Container logs as a string
        """
        container = self.get_container(container_id)
        if not container:
            return "Container not found"
            
        # Generate mock logs
        logs = []
        now = datetime.now()
        
        if container['Names'][0] == '/web-server':
            # Nginx-style logs
            for i in range(tail):
                time_str = (now - timedelta(seconds=i*60)).strftime('%d/%b/%Y:%H:%M:%S +0000')
                logs.append(f'192.168.1.{random.randint(2, 254)} - - [{time_str}] "GET /index.html HTTP/1.1" 200 {random.randint(500, 5000)} "-" "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"')
                
        elif container['Names'][0] == '/database':
            # Postgres-style logs
            for i in range(tail):
                time_str = (now - timedelta(seconds=i*30)).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
                logs.append(f'{time_str} UTC [1234] LOG:  duration: {random.randint(1, 1000)}.{random.randint(1, 999)} ms  statement: SELECT * FROM users WHERE id = {random.randint(1, 1000)};')
                
        elif container['Names'][0] == '/backend-api':
            # Node.js logs
            for i in range(tail):
                time_str = (now - timedelta(seconds=i*45)).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
                logs.append(f'{time_str} INFO  [Server] Request received: GET /api/users/{random.randint(1, 1000)} from 192.168.1.{random.randint(2, 254)}')
                
        elif container['Names'][0] == '/redis-cache':
            # Redis logs
            for i in range(tail):
                time_str = (now - timedelta(seconds=i*20)).strftime('%d %b %H:%M:%S.%f')[:-3]
                logs.append(f'{time_str} * 1 "GET" "user:{random.randint(1, 1000)}"')
                
        else:
            # Generic logs
            for i in range(tail):
                time_str = (now - timedelta(seconds=i*60)).strftime('%Y-%m-%d %H:%M:%S')
                logs.append(f'{time_str} [INFO] Process completed successfully with status code 0')
                
        # Reverse logs to show newest first
        logs.reverse()
        return '\n'.join(logs)
        
    def get_container_file_tree(self, container_id: str, path: str = '/') -> List[Dict[str, Any]]:
        """
        Get mock file tree for a container.
        
        Args:
            container_id: Container ID or name
            path: Path inside the container
            
        Returns:
            List of file dictionaries
        """
        if container_id in self.mock_files and path in self.mock_files[container_id]:
            return self.mock_files[container_id][path]
            
        # For root path, show actual project files
        if path == '/':
            return [
                {'name': 'assets', 'type': 'directory', 'size': '4096', 'permissions': 'drwxr-xr-x', 'path': '/assets'},
                {'name': 'core', 'type': 'directory', 'size': '4096', 'permissions': 'drwxr-xr-x', 'path': '/core'},
                {'name': 'ui', 'type': 'directory', 'size': '4096', 'permissions': 'drwxr-xr-x', 'path': '/ui'},
                {'name': 'utils', 'type': 'directory', 'size': '4096', 'permissions': 'drwxr-xr-x', 'path': '/utils'},
                {'name': 'main.py', 'type': 'file', 'size': '3217', 'permissions': '-rw-r--r--', 'path': '/main.py'},
                {'name': 'pyproject.toml', 'type': 'file', 'size': '516', 'permissions': '-rw-r--r--', 'path': '/pyproject.toml'},
                {'name': 'code_explorer.py', 'type': 'file', 'size': '6534', 'permissions': '-rw-r--r--', 'path': '/ui/code_explorer.py'},
                {'name': 'sidebar.py', 'type': 'file', 'size': '5431', 'permissions': '-rw-r--r--', 'path': '/ui/sidebar.py'}
            ]
        # For core directory
        elif path == '/core':
            return [
                {'name': '__init__.py', 'type': 'file', 'size': '85', 'permissions': '-rw-r--r--', 'path': '/core/__init__.py'},
                {'name': 'docker_client.py', 'type': 'file', 'size': '12356', 'permissions': '-rw-r--r--', 'path': '/core/docker_client.py'},
                {'name': 'mock_docker_client.py', 'type': 'file', 'size': '15784', 'permissions': '-rw-r--r--', 'path': '/core/mock_docker_client.py'},
                {'name': 'monitor.py', 'type': 'file', 'size': '7824', 'permissions': '-rw-r--r--', 'path': '/core/monitor.py'}
            ]
        # For ui directory
        elif path == '/ui':
            return [
                {'name': '__init__.py', 'type': 'file', 'size': '85', 'permissions': '-rw-r--r--', 'path': '/ui/__init__.py'},
                {'name': 'app.py', 'type': 'file', 'size': '8765', 'permissions': '-rw-r--r--', 'path': '/ui/app.py'},
                {'name': 'components.py', 'type': 'file', 'size': '12987', 'permissions': '-rw-r--r--', 'path': '/ui/components.py'},
                {'name': 'containers.py', 'type': 'file', 'size': '18754', 'permissions': '-rw-r--r--', 'path': '/ui/containers.py'},
                {'name': 'metrics.py', 'type': 'file', 'size': '14568', 'permissions': '-rw-r--r--', 'path': '/ui/metrics.py'},
                {'name': 'reports.py', 'type': 'file', 'size': '15678', 'permissions': '-rw-r--r--', 'path': '/ui/reports.py'},
                {'name': 'sidebar.py', 'type': 'file', 'size': '5487', 'permissions': '-rw-r--r--', 'path': '/ui/sidebar.py'}
            ]
        # For utils directory
        elif path == '/utils':
            return [
                {'name': '__init__.py', 'type': 'file', 'size': '85', 'permissions': '-rw-r--r--', 'path': '/utils/__init__.py'},
                {'name': 'config.py', 'type': 'file', 'size': '3456', 'permissions': '-rw-r--r--', 'path': '/utils/config.py'},
                {'name': 'compat.py', 'type': 'file', 'size': '2178', 'permissions': '-rw-r--r--', 'path': '/utils/compat.py'},
                {'name': 'theme.py', 'type': 'file', 'size': '4567', 'permissions': '-rw-r--r--', 'path': '/utils/theme.py'}
            ]
        # For assets directory
        elif path == '/assets':
            return [
                {'name': '__init__.py', 'type': 'file', 'size': '85', 'permissions': '-rw-r--r--', 'path': '/assets/__init__.py'},
                {'name': 'icons.py', 'type': 'file', 'size': '8756', 'permissions': '-rw-r--r--', 'path': '/assets/icons.py'},
                {'name': 'svg', 'type': 'directory', 'size': '4096', 'permissions': 'drwxr-xr-x', 'path': '/assets/svg'}
            ]
        # Generate generic mock files for unknown containers/paths
        else:
            return [
                {'name': 'etc', 'type': 'directory', 'size': '4096', 'permissions': 'drwxr-xr-x', 'path': '/etc'},
                {'name': 'var', 'type': 'directory', 'size': '4096', 'permissions': 'drwxr-xr-x', 'path': '/var'},
                {'name': 'usr', 'type': 'directory', 'size': '4096', 'permissions': 'drwxr-xr-x', 'path': '/usr'},
                {'name': 'bin', 'type': 'directory', 'size': '4096', 'permissions': 'drwxr-xr-x', 'path': '/bin'},
                {'name': 'app', 'type': 'directory', 'size': '4096', 'permissions': 'drwxr-xr-x', 'path': '/app'}
            ]
        
    def read_container_file(self, container_id: str, file_path: str) -> str:
        """
        Read mock file content from a container.
        
        Args:
            container_id: Container ID or name
            file_path: Path to the file inside the container
            
        Returns:
            File content as a string or error message
        """
        if container_id in self.mock_file_contents and file_path in self.mock_file_contents[container_id]:
            return self.mock_file_contents[container_id][file_path]
        
        # Special paths for actual project files
        if file_path == '/main.py':
            return """#!/usr/bin/env python3
'''
Dockify - Docker Container Monitoring Application
A Spotify-inspired desktop application for monitoring Docker containers.

Developed for a university diploma project, Dockify provides intuitive
container management, performance metrics visualization, and resource
optimization recommendations for Docker environments on Ubuntu.

Features:
- Real-time container monitoring (CPU, memory, network usage)
- Container management (start, stop, restart, remove)
- Customizable alerts for resource thresholds
- Code explorer for examining container files
- Metrics visualization and reporting
- Modern, Spotify-inspired UI/UX design
'''

import os
import sys
import logging
import argparse
from typing import List, Dict, Any, Optional

import customtkinter as ctk
from tkinter import messagebox

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('dockify')

def check_dependencies() -> bool:
    '''Check if all required dependencies are installed.'''
    try:
        import docker
        import psutil
        import pandas
        import plotly
        import pygments
        return True
    except ImportError as e:
        messagebox.showerror(
            "Missing Dependencies",
            f"Required dependency missing: {e}\\n\\n"
            "Please install all dependencies using:\\n"
            "pip install -r requirements.txt"
        )
        return False

def main() -> None:
    '''Main function to initialize and run the application.'''
    # Import here to avoid circular imports
    from ui.app import DockifyApp
    
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Dockify - Docker Container Monitoring Application')
    parser.add_argument("-d", "--demo", action="store_true", help="Run the application in demo mode with simulated data")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging (DEBUG level)")
    args = parser.parse_args()
    
    # Set log level based on args
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Set appearance mode and default color theme
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    
    # Check for demo mode
    if args.demo:
        logger.info("Starting application in demo mode")
        
    # Initialize Docker client with demo mode if specified
    if args.demo:
        # Import here to avoid circular imports
        from core.mock_docker_client import MockDockerClient
        docker_client = MockDockerClient()
        logger.info("Created MockDockerClient for demo mode")
        
        # Create app with explicit demo mode
        app = DockifyApp(docker_client=docker_client, force_demo=True)
    else:
        # Create the app normally
        app = DockifyApp()
    
    # Run the app
    try:
        app.mainloop()
    except Exception as e:
        logger.error(f"Application crashed: {e}")
        raise

if __name__ == "__main__":
    main()
"""
        elif file_path == '/core/docker_client.py':
            return """'''
Docker client wrapper for Dockify.
Provides a simplified interface to interact with Docker containers and images.
'''

import logging
import time
import json
from typing import List, Dict, Any, Optional, Union, Tuple
from datetime import datetime

import docker
from docker.errors import DockerException, APIError, NotFound

logger = logging.getLogger('dockify.docker_client')

class DockerClient:
    '''
    Docker client wrapper for Dockify.
    Provides a simplified interface to interact with Docker containers and images.
    '''
    def __init__(self, base_url: Optional[str] = None):
        '''
        Initialize the Docker client.
        
        Args:
            base_url: Docker daemon URL
        '''
        try:
            if base_url:
                self.client = docker.DockerClient(base_url=base_url)
            else:
                self.client = docker.from_env()
                
            # Test connection
            self.client.ping()
            logger.info("Successfully connected to Docker daemon")
        except DockerException as e:
            logger.error(f"Failed to connect to Docker daemon: {e}")
            raise
            
    def list_containers(self, all: bool = False) -> List[Dict[str, Any]]:
        '''
        List all containers.
        
        Args:
            all: Whether to include stopped containers
            
        Returns:
            List of container dictionaries
        '''
        try:
            containers = self.client.containers.list(all=all)
            result = []
            
            for container in containers:
                # Convert container to dictionary
                container_dict = {
                    'Id': container.id,
                    'Names': [f"/{container.name}"],
                    'Image': container.image.tags[0] if container.image.tags else container.image.id,
                    'ImageID': container.image.id,
                    'Command': container.attrs.get('Config', {}).get('Cmd', [''])[0] if container.attrs.get('Config', {}).get('Cmd') else '',
                    'Created': container.attrs.get('Created', ''),
                    'State': container.status,
                    'Status': container.status,
                    'Ports': self._extract_ports(container),
                    'Labels': container.labels,
                    'NetworkSettings': container.attrs.get('NetworkSettings', {})
                }
                result.append(container_dict)
                
            return result
        except DockerException as e:
            logger.error(f"Failed to list containers: {e}")
            return []
        
    def _extract_ports(self, container) -> List[Dict[str, Any]]:
        '''
        Extract port mappings from container.
        
        Args:
            container: Docker container
            
        Returns:
            List of port dictionaries
        '''
        ports = []
        
        try:
            # Get port mappings from container attributes
            port_bindings = container.attrs.get('HostConfig', {}).get('PortBindings', {})
            
            for container_port, host_ports in port_bindings.items():
                proto = container_port.split('/')[-1]
                port = int(container_port.split('/')[0])
                
                for host_port in host_ports:
                    ports.append({
                        'PrivatePort': port,
                        'PublicPort': int(host_port.get('HostPort', 0)),
                        'Type': proto
                    })
                    
            return ports
        except Exception as e:
            logger.error(f"Failed to extract ports: {e}")
            return []
            
    def start_container(self, container_id: str) -> bool:
        '''
        Start a container.
        
        Args:
            container_id: Container ID or name
            
        Returns:
            True if successful, False otherwise
        '''
        try:
            container = self.client.containers.get(container_id)
            container.start()
            logger.info(f"Started container {container_id}")
            return True
        except DockerException as e:
            logger.error(f"Failed to start container {container_id}: {e}")
            return False
            
    def stop_container(self, container_id: str) -> bool:
        '''
        Stop a container.
        
        Args:
            container_id: Container ID or name
            
        Returns:
            True if successful, False otherwise
        '''
        try:
            container = self.client.containers.get(container_id)
            container.stop()
            logger.info(f"Stopped container {container_id}")
            return True
        except DockerException as e:
            logger.error(f"Failed to stop container {container_id}: {e}")
            return False
            
    def restart_container(self, container_id: str) -> bool:
        '''
        Restart a container.
        
        Args:
            container_id: Container ID or name
            
        Returns:
            True if successful, False otherwise
        '''
        try:
            container = self.client.containers.get(container_id)
            container.restart()
            logger.info(f"Restarted container {container_id}")
            return True
        except DockerException as e:
            logger.error(f"Failed to restart container {container_id}: {e}")
            return False
            
    def remove_container(self, container_id: str, force: bool = False) -> bool:
        '''
        Remove a container.
        
        Args:
            container_id: Container ID or name
            force: Whether to force removal of a running container
            
        Returns:
            True if successful, False otherwise
        '''
        try:
            container = self.client.containers.get(container_id)
            container.remove(force=force)
            logger.info(f"Removed container {container_id}")
            return True
        except DockerException as e:
            logger.error(f"Failed to remove container {container_id}: {e}")
            return False
            
    def get_container_stats(self, container_id: str) -> Dict[str, Any]:
        '''
        Get container stats.
        
        Args:
            container_id: Container ID or name
            
        Returns:
            Dictionary with container stats
        '''
        try:
            container = self.client.containers.get(container_id)
            stats = container.stats(stream=False)
            
            # Calculate CPU percentage
            cpu_percent = self._calculate_cpu_percentage(stats)
            
            # Extract memory usage
            memory_usage = stats.get('memory_stats', {}).get('usage', 0)
            memory_limit = stats.get('memory_stats', {}).get('limit', 0)
            memory_percent = (memory_usage / memory_limit) * 100 if memory_limit else 0
            
            # Extract network usage
            networks = stats.get('networks', {})
            network_rx = 0
            network_tx = 0
            
            for network in networks.values():
                network_rx += network.get('rx_bytes', 0)
                network_tx += network.get('tx_bytes', 0)
                
            return {
                'cpu_percent': cpu_percent,
                'memory_usage': memory_usage,
                'memory_limit': memory_limit,
                'memory_percent': memory_percent,
                'network_rx': network_rx,
                'network_tx': network_tx,
                'timestamp': time.time()
            }
        except DockerException as e:
            logger.error(f"Failed to get stats for container {container_id}: {e}")
            return {}
            
    def _calculate_cpu_percentage(self, stats: Dict[str, Any]) -> float:
        '''
        Calculate CPU percentage from stats.
        
        Args:
            stats: Container stats dictionary
            
        Returns:
            CPU percentage
        '''
        try:
            cpu_delta = stats.get('cpu_stats', {}).get('cpu_usage', {}).get('total_usage', 0) - \
                       stats.get('precpu_stats', {}).get('cpu_usage', {}).get('total_usage', 0)
            
            system_delta = stats.get('cpu_stats', {}).get('system_cpu_usage', 0) - \
                          stats.get('precpu_stats', {}).get('system_cpu_usage', 0)
            
            online_cpus = stats.get('cpu_stats', {}).get('online_cpus', 0)
            
            if system_delta > 0 and online_cpus > 0:
                return (cpu_delta / system_delta) * online_cpus * 100.0
            else:
                return 0.0
        except Exception as e:
            logger.error(f"Failed to calculate CPU percentage: {e}")
            return 0.0
            
    def inspect_container(self, container_id: str) -> Dict[str, Any]:
        '''
        Inspect a container.
        
        Args:
            container_id: Container ID or name
            
        Returns:
            Dictionary with container details
        '''
        try:
            container = self.client.containers.get(container_id)
            return container.attrs
        except DockerException as e:
            logger.error(f"Failed to inspect container {container_id}: {e}")
            return {}
            
    def list_images(self) -> List[Dict[str, Any]]:
        '''
        List all images.
        
        Returns:
            List of image dictionaries
        '''
        try:
            images = self.client.images.list()
            result = []
            
            for image in images:
                # Convert image to dictionary
                image_dict = {
                    'Id': image.id,
                    'RepoTags': image.tags,
                    'Created': image.attrs.get('Created', ''),
                    'Size': image.attrs.get('Size', 0),
                    'VirtualSize': image.attrs.get('VirtualSize', 0),
                    'Labels': image.labels
                }
                result.append(image_dict)
                
            return result
        except DockerException as e:
            logger.error(f"Failed to list images: {e}")
            return []
            
    def get_container_logs(self, container_id: str, tail: int = 100) -> str:
        '''
        Get container logs.
        
        Args:
            container_id: Container ID or name
            tail: Number of log lines to return
            
        Returns:
            Container logs as a string
        '''
        try:
            container = self.client.containers.get(container_id)
            logs = container.logs(tail=tail, timestamps=True).decode('utf-8', errors='replace')
            return logs
        except DockerException as e:
            logger.error(f"Failed to get logs for container {container_id}: {e}")
            return f"Error retrieving logs: {e}"
            
    def get_container_file_tree(self, container_id: str, path: str = '/') -> List[Dict[str, Any]]:
        '''
        Get container file tree (directory listing).
        
        Args:
            container_id: Container ID or name
            path: Path inside the container
            
        Returns:
            List of file dictionaries
        '''
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
        '''
        Read file content from a container.
        
        Args:
            container_id: Container ID or name
            file_path: Path to the file inside the container
            
        Returns:
            File content as a string or error message
        '''
        try:
            container = self.client.containers.get(container_id)
            exec_result = container.exec_run(f"cat {file_path}")
            
            if exec_result.exit_code != 0:
                return f"Error reading file: {exec_result.output.decode('utf-8', errors='replace')}"
                
            return exec_result.output.decode('utf-8', errors='replace')
        except DockerException as e:
            logger.error(f"Failed to read file {file_path} from container {container_id}: {e}")
            return f"Error reading file: {e}"
            
    def get_container_processes(self, container_id: str) -> List[Dict[str, Any]]:
        '''
        Get running processes in a container.
        
        Args:
            container_id: Container ID or name
            
        Returns:
            List of process dictionaries
        '''
        try:
            container = self.client.containers.get(container_id)
            exec_result = container.exec_run("ps -ef")
            
            if exec_result.exit_code != 0:
                logger.error(f"Failed to get processes for container {container_id}: {exec_result.output}")
                return []
                
            output = exec_result.output.decode('utf-8', errors='replace')
            processes = []
            
            # Parse ps -ef output
            lines = output.splitlines()
            if len(lines) > 0:
                # Get headers
                headers = lines[0].split()
                
                # Parse processes
                for line in lines[1:]:
                    parts = line.split()
                    if len(parts) >= len(headers):
                        process = {}
                        
                        # Map parts to headers
                        for i, header in enumerate(headers):
                            if i < len(parts):
                                process[header.lower()] = parts[i]
                            
                        # Join remaining parts as command
                        if len(parts) > len(headers):
                            process['cmd'] = ' '.join(parts[len(headers):])
                            
                        processes.append(process)
                        
            return processes
        except DockerException as e:
            logger.error(f"Failed to get processes for container {container_id}: {e}")
            return []
            
    def info(self) -> Dict[str, Any]:
        '''
        Get Docker system information.
        
        Returns:
            Dictionary with Docker system info
        '''
        try:
            return self.client.info()
        except DockerException as e:
            logger.error(f"Failed to get Docker info: {e}")
            return {}
"""
        elif file_path == '/ui/app.py':
            return """'''
Main application window for Dockify.
'''

import os
import logging
import threading
import time
from typing import Dict, List, Any, Optional, Callable

import customtkinter as ctk
from tkinter import messagebox

from core.docker_client import DockerClient
from core.mock_docker_client import MockDockerClient
from core.monitor import ContainerMonitor
from ui.sidebar import Sidebar
from ui.overview import OverviewFrame
from ui.containers import ContainersFrame
from ui.metrics import MetricsFrame
from ui.reports import ReportsFrame
from utils.config import Config
from utils.theme import apply_theme, SPOTIFY_COLORS

logger = logging.getLogger('dockify.app')

class DockifyApp(ctk.CTk):
    '''
    Main application window for Dockify Docker container management.
    '''
    def __init__(self, docker_client: Optional[DockerClient] = None, force_demo: bool = False):
        '''
        Initialize the application.
        
        Args:
            docker_client: Docker client instance (optional)
            force_demo: Whether to force demo mode (optional)
        '''
        super().__init__()
        
        # Load configuration
        self.config = Config()
        
        # Apply theme
        apply_theme()
        
        # Set up docker client
        self.docker_client = self._initialize_docker_client(docker_client, force_demo)
        
        # Start container monitor
        self.container_monitor = ContainerMonitor(self.docker_client)
        
        # Set up UI
        self.title("Dockify - Docker Container Management")
        self.geometry("1200x800")
        self.minsize(900, 600)
        
        # Configure grid
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Create sidebar
        self.sidebar = Sidebar(self)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        # Create content frames
        self.frames = {}
        
        # Overview frame
        self.frames["overview"] = OverviewFrame(self, self.docker_client)
        
        # Containers frame
        self.frames["containers"] = ContainersFrame(self, self.docker_client)
        
        # Metrics frame
        self.frames["metrics"] = MetricsFrame(self, self.docker_client, self.container_monitor)
        
        # Reports frame
        self.frames["reports"] = ReportsFrame(self, self.docker_client, self.container_monitor)
        
        # Show default frame
        self.current_frame = None
        self.sidebar.select_button("overview")
        
        # Set up auto-refresh
        self._setup_auto_refresh()
        
        # Set up metrics update
        self._setup_metrics_update()
        
        # Register cleanup
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        
    def _initialize_docker_client(self, docker_client: Optional[DockerClient], force_demo: bool) -> DockerClient:
        '''
        Initialize Docker client or use provided one.
        
        Args:
            docker_client: Docker client instance (optional)
            force_demo: Whether to force demo mode (optional)
            
        Returns:
            DockerClient instance
        '''
        if docker_client:
            logger.info("Using pre-initialized Docker client")
            return docker_client
            
        # Try to connect to Docker or fall back to demo mode
        try:
            if force_demo:
                raise Exception("Demo mode forced")
                
            docker_client = DockerClient()
            logger.info("Connected to Docker daemon")
            return docker_client
        except Exception as e:
            logger.warning(f"Docker connection failed: {e}. Falling back to demo mode.")
            messagebox.showwarning(
                "Docker Connection Failed",
                "Could not connect to Docker daemon. Running in demo mode with simulated data."
            )
            return MockDockerClient()
            
    def show_frame(self, name: str) -> None:
        '''
        Show a frame by name.
        
        Args:
            name: Frame name
        '''
        if name in self.frames:
            # Hide current frame
            if self.current_frame is not None:
                self.frames[self.current_frame].grid_forget()
                
            # Show new frame
            self.frames[name].grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
            self.frames[name].refresh()
            self.current_frame = name
            
    def _setup_auto_refresh(self) -> None:
        '''Set up auto-refresh for container lists.'''
        
        def refresh_visible_frame():
            # Refresh current frame if visible
            if self.current_frame and hasattr(self.frames[self.current_frame], 'refresh'):
                self.frames[self.current_frame].refresh()
            
            # Schedule next refresh
            self.after(5000, refresh_visible_frame)
            
        # Start auto-refresh
        self.after(5000, refresh_visible_frame)
        
    def _setup_metrics_update(self) -> None:
        '''Set up metrics update listener.'''
        
        def update_metrics():
            while True:
                # Get metrics
                metrics = self.container_monitor.get_current_metrics()
                
                # Update UI frames
                self.after(0, lambda m=metrics: self._update_ui_metrics(m))
                
                # Wait for next update
                time.sleep(1)
                
        # Start metrics update thread
        threading.Thread(target=update_metrics, daemon=True).start()
        
    def _update_ui_metrics(self, metrics: Dict[str, Dict[str, Any]]) -> None:
        '''
        Update UI metrics.
        
        Args:
            metrics: Dictionary of container metrics
        '''
        # Update containers frame
        if "containers" in self.frames:
            self.frames["containers"].update_metrics(metrics)
            
        # Update metrics frame
        if "metrics" in self.frames:
            self.frames["metrics"].update_metrics(metrics)
            
        # Update overview frame
        if "overview" in self.frames:
            self.frames["overview"].update_metrics(metrics)
            
    def _on_close(self) -> None:
        '''Handle application close.'''
        try:
            # Stop container monitor
            if hasattr(self, 'container_monitor'):
                self.container_monitor.stop()
                
            # Save configuration
            if hasattr(self, 'config'):
                self.config.save()
                
            # Destroy window
            self.destroy()
        except Exception as e:
            logger.error(f"Error during application shutdown: {e}")
            self.destroy()
"""
        elif file_path == '/ui/sidebar.py':
            return """'''
Sidebar navigation for Dockify.
'''

import logging
from typing import Dict, Any, Callable

import customtkinter as ctk

from assets.icons import get_icon_image
from utils.theme import SPOTIFY_COLORS, lighten_color

logger = logging.getLogger('dockify.ui.sidebar')

class Sidebar(ctk.CTkFrame):
    '''
    Sidebar navigation component for the Dockify application.
    '''
    def __init__(self, parent):
        '''
        Initialize sidebar.
        
        Args:
            parent: Parent window
        '''
        super().__init__(parent, width=200, corner_radius=0, fg_color=SPOTIFY_COLORS["sidebar"])
        self.parent = parent
        
        # Set fixed width
        self.pack_propagate(False)
        
        # Current active section
        self.active_section = None
        self.buttons = {}
        
        # Create UI
        self.create_ui()
        
    def create_ui(self):
        '''Create and setup the sidebar UI.'''
        try:
            # Add logo and title at the top
            logo_frame = ctk.CTkFrame(self, fg_color="transparent", height=60)
            logo_frame.pack(fill="x", pady=(15, 5))
            
            # Logo icon
            docker_icon = get_icon_image("docker", size=32, color=SPOTIFY_COLORS["accent"])
            logo_label = ctk.CTkLabel(logo_frame, text="", image=docker_icon)
            logo_label.pack(side="left", padx=(15, 5))
            
            # App title
            title_label = ctk.CTkLabel(
                logo_frame, 
                text="Dockify", 
                font=("Helvetica", 22, "bold"),
                text_color=SPOTIFY_COLORS["text_bright"]
            )
            title_label.pack(side="left")
            
            # Separator
            separator = ctk.CTkFrame(self, height=1, fg_color=SPOTIFY_COLORS["border"])
            separator.pack(fill="x", padx=15, pady=(5, 15))
            
            # Navigation buttons
            self.create_nav_button("overview", "Dashboard", "dashboard")
            self.create_nav_button("containers", "Containers", "container")
            self.create_nav_button("metrics", "Metrics", "chart")
            self.create_nav_button("reports", "Reports", "file")
            
            # Bottom section with version info
            version_frame = ctk.CTkFrame(self, fg_color="transparent", height=40)
            version_frame.pack(fill="x", side="bottom", pady=10)
            
            version_label = ctk.CTkLabel(
                version_frame, 
                text="v1.0.0", 
                font=("Helvetica", 10),
                text_color=SPOTIFY_COLORS["text_subtle"]
            )
            version_label.pack(side="right", padx=15)
            
        except Exception as e:
            logger.error(f"Error creating sidebar UI: {e}")
            
    def create_nav_button(self, section: str, text: str, icon_name: str):
        '''
        Create a navigation button.
        
        Args:
            section: Section identifier
            text: Button text
            icon_name: Icon name
        '''
        try:
            # Create frame to hold button content
            button_frame = ctk.CTkFrame(self, fg_color="transparent")
            button_frame.pack(fill="x", pady=2)
            
            # Create hover effect color
            hover_color = lighten_color(SPOTIFY_COLORS["sidebar"], 0.03)
            active_color = lighten_color(SPOTIFY_COLORS["sidebar"], 0.06)
            
            # Create the button
            button = ctk.CTkButton(
                button_frame,
                text=text,
                font=("Helvetica", 14),
                text_color=SPOTIFY_COLORS["text_bright"],
                fg_color="transparent",
                hover_color=hover_color,
                anchor="w",
                height=36,
                corner_radius=4,
                image=get_icon_image(icon_name, size=20, color=SPOTIFY_COLORS["text_bright"]),
                command=lambda s=section: self.select_button(s)
            )
            button.pack(fill="x", padx=(10, 10))
            
            # Store button for later reference
            self.buttons[section] = {
                "button": button,
                "frame": button_frame,
                "active_color": active_color
            }
            
        except Exception as e:
            logger.error(f"Error creating navigation button {section}: {e}")
            
    def select_button(self, section: str):
        '''
        Select a navigation button and show corresponding section.
        
        Args:
            section: Section identifier
        '''
        try:
            # Reset previous active button
            if self.active_section and self.active_section in self.buttons:
                self.buttons[self.active_section]["button"].configure(
                    fg_color="transparent",
                    text_color=SPOTIFY_COLORS["text_bright"]
                )
                
            # Set new active button
            if section in self.buttons:
                self.buttons[section]["button"].configure(
                    fg_color=self.buttons[section]["active_color"],
                    text_color=SPOTIFY_COLORS["accent"]
                )
                
            # Update active section
            self.active_section = section
            
            # Show corresponding frame
            self.parent.show_frame(section)
            
        except Exception as e:
            logger.error(f"Error selecting button {section}: {e}")
"""
        elif file_path == '/ui/metrics.py':
            return """'''
Metrics visualization for Dockify.
Shows performance metrics over time with interactive charts.
'''

import os
import logging
import time
import datetime
import threading
from typing import Dict, List, Any, Optional, Tuple, Callable

import customtkinter as ctk
import tkinter as tk
from tkinter import ttk

from utils.theme import SPOTIFY_COLORS, lighten_color
from core.docker_client import DockerClient
from core.monitor import ContainerMonitor

logger = logging.getLogger('dockify.ui.metrics')

class MetricsFrame(ctk.CTkFrame):
    '''
    Metrics visualization screen for analyzing container performance over time.
    '''
    def __init__(self, parent, docker_client: Any, container_monitor: ContainerMonitor):
        '''
        Initialize the metrics visualization screen.
        
        Args:
            parent: Parent widget
            docker_client: Docker client instance
            container_monitor: Container monitor instance
        '''
        super().__init__(parent, corner_radius=0, fg_color=SPOTIFY_COLORS["background"])
        self.parent = parent
        self.docker_client = docker_client
        self.container_monitor = container_monitor
        
        # Current container and metrics
        self.selected_container = None
        self.current_metrics = {}
        
        # Create UI
        self.create_ui()
        
    def create_ui(self):
        '''Create and setup the user interface.'''
        try:
            # Main content layout
            self.grid_columnconfigure(0, weight=1)
            self.grid_rowconfigure(1, weight=1)
            
            # Header section
            header_frame = ctk.CTkFrame(self, fg_color="transparent", height=70)
            header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 0))
            
            # Container selection
            container_select_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
            container_select_frame.pack(side="left", fill="y")
            
            container_label = ctk.CTkLabel(
                container_select_frame, 
                text="Container:", 
                font=("Helvetica", 14),
                text_color=SPOTIFY_COLORS["text_bright"]
            )
            container_label.pack(side="left", padx=(0, 10))
            
            self.container_var = tk.StringVar()
            self.container_selector = ctk.CTkOptionMenu(
                container_select_frame,
                values=["Loading containers..."],
                variable=self.container_var,
                width=250,
                font=("Helvetica", 14),
                dropdown_font=("Helvetica", 14),
                fg_color=SPOTIFY_COLORS["button"],
                button_color=SPOTIFY_COLORS["button"],
                button_hover_color=lighten_color(SPOTIFY_COLORS["button"], 0.1),
                command=self.on_container_selected
            )
            self.container_selector.pack(side="left")
            
            # Time range selection
            time_range_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
            time_range_frame.pack(side="right", fill="y")
            
            time_label = ctk.CTkLabel(
                time_range_frame, 
                text="Time range:", 
                font=("Helvetica", 14),
                text_color=SPOTIFY_COLORS["text_bright"]
            )
            time_label.pack(side="left", padx=(0, 10))
            
            self.time_range_var = tk.StringVar(value="Last 5 minutes")
            time_ranges = ["Last 5 minutes", "Last 15 minutes", "Last hour", "All"]
            self.time_range_selector = ctk.CTkOptionMenu(
                time_range_frame,
                values=time_ranges,
                variable=self.time_range_var,
                width=150,
                font=("Helvetica", 14),
                dropdown_font=("Helvetica", 14),
                fg_color=SPOTIFY_COLORS["button"],
                button_color=SPOTIFY_COLORS["button"],
                button_hover_color=lighten_color(SPOTIFY_COLORS["button"], 0.1),
                command=self.refresh_graphs
            )
            self.time_range_selector.pack(side="left")
            
            # Content area with graphs
            content_frame = ctk.CTkFrame(self, fg_color=SPOTIFY_COLORS["card"])
            content_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=20)
            content_frame.grid_columnconfigure(0, weight=1)
            content_frame.grid_rowconfigure((0, 1), weight=1)
            
            # CPU usage chart
            cpu_frame = ctk.CTkFrame(content_frame, fg_color=SPOTIFY_COLORS["card_secondary"])
            cpu_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
            
            cpu_title = ctk.CTkLabel(
                cpu_frame, 
                text="CPU Usage", 
                font=("Helvetica", 16, "bold"),
                text_color=SPOTIFY_COLORS["text_bright"]
            )
            cpu_title.pack(anchor="w", padx=15, pady=(15, 5))
            
            # Create charts - in a real application, this would use a browser widget
            # for interactive charts, but for simplicity, we'll use text
            
            # CPU chart placeholder
            self.cpu_chart_placeholder = ctk.CTkLabel(
                cpu_frame,
                text="No container selected",
                font=("Helvetica", 14),
                text_color=SPOTIFY_COLORS["text_subtle"]
            )
            self.cpu_chart_placeholder.pack(expand=True, fill="both", padx=15, pady=15)
            
            # For text-based ASCII chart
            self.cpu_text = ctk.CTkTextbox(
                cpu_frame,
                font=("Courier", 12),
                fg_color=SPOTIFY_COLORS["card_secondary"],
                text_color=SPOTIFY_COLORS["text_bright"],
                height=300,
                wrap="none"
            )
            
            # Memory usage chart
            memory_frame = ctk.CTkFrame(content_frame, fg_color=SPOTIFY_COLORS["card_secondary"])
            memory_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
            
            memory_title = ctk.CTkLabel(
                memory_frame, 
                text="Memory Usage", 
                font=("Helvetica", 16, "bold"),
                text_color=SPOTIFY_COLORS["text_bright"]
            )
            memory_title.pack(anchor="w", padx=15, pady=(15, 5))
            
            # Memory chart placeholder
            self.memory_chart_placeholder = ctk.CTkLabel(
                memory_frame,
                text="No container selected",
                font=("Helvetica", 14),
                text_color=SPOTIFY_COLORS["text_subtle"]
            )
            self.memory_chart_placeholder.pack(expand=True, fill="both", padx=15, pady=15)
            
            # For text-based ASCII chart
            self.memory_text = ctk.CTkTextbox(
                memory_frame,
                font=("Courier", 12),
                fg_color=SPOTIFY_COLORS["card_secondary"],
                text_color=SPOTIFY_COLORS["text_bright"],
                height=300,
                wrap="none"
            )
            
            # Initial refresh
            self.refresh()
            
        except Exception as e:
            logger.error(f"Error creating metrics UI: {e}")
            
    def refresh(self):
        '''Refresh container list and graphs.'''
        # Load containers
        threading.Thread(target=self.load_containers, daemon=True).start()
        
        # Refresh graphs if container selected
        if self.selected_container:
            self.refresh_graphs()
            
    def load_containers(self):
        '''Load container list in a background thread.'''
        try:
            # Get containers
            containers = self.docker_client.list_containers()
            
            # Update UI in main thread
            self.after(0, lambda: self.update_container_selector(containers))
            
        except Exception as e:
            logger.error(f"Error loading containers: {e}")
            
    def update_container_selector(self, containers):
        '''
        Update the container selector dropdown.
        
        Args:
            containers: List of container dictionaries
        '''
        try:
            # Create container map (name -> id)
            container_map = {}
            
            for container in containers:
                container_id = container.get('Id', '')
                container_name = container.get('Names', [''])[0].lstrip('/')
                
                if container_name:
                    display_name = f"{container_name} ({container_id[:12]})"
                    container_map[display_name] = container_id
                    
            # Update dropdown values
            if container_map:
                # Store previous selection
                prev_selection = self.container_var.get()
                
                # Set new values
                self.container_selector.configure(values=list(container_map.keys()))
                
                # Try to restore previous selection or set to first item
                if prev_selection in container_map:
                    self.container_var.set(prev_selection)
                else:
                    self.container_var.set(next(iter(container_map), ""))
                    self.selected_container = container_map.get(self.container_var.get())
                    
                # Refresh graphs
                if self.selected_container:
                    self.refresh_graphs()
            else:
                # No containers available
                self.container_selector.configure(values=["No running containers"])
                self.container_var.set("No running containers")
                self.selected_container = None
                
            # Store container map for future reference
            self.container_map = container_map
            
        except Exception as e:
            logger.error(f"Error updating container selector: {e}")
            
    def on_container_selected(self, container_name):
        '''
        Handle container selection change.
        
        Args:
            container_name: Selected container display name
        '''
        try:
            # Get container ID from name
            if container_name in getattr(self, 'container_map', {}):
                self.selected_container = self.container_map[container_name]
                self.refresh_graphs()
            else:
                self.selected_container = None
                # Hide charts
                self.cpu_chart_placeholder.configure(text="No container selected")
                self.cpu_chart_placeholder.pack(expand=True, fill="both", padx=15, pady=15)
                self.cpu_text.pack_forget()
                
                self.memory_chart_placeholder.configure(text="No container selected")
                self.memory_chart_placeholder.pack(expand=True, fill="both", padx=15, pady=15)
                self.memory_text.pack_forget()
                
        except Exception as e:
            logger.error(f"Error selecting container: {e}")
            
    def refresh_graphs(self, *args):
        '''Refresh graph visualizations.'''
        # Generate graphs in background thread
        threading.Thread(target=self.generate_graphs, daemon=True).start()
        
    def generate_graphs(self):
        '''Generate graph visualizations in a background thread.'''
        try:
            # Update UI in main thread
            self.after(0, self.update_graph_ui)
            
        except Exception as e:
            logger.error(f"Error generating graphs: {e}")
            
    def update_graph_ui(self):
        '''Update graph UI with generated HTML.'''
        try:
            if not self.selected_container:
                # Show placeholders
                self.cpu_chart_placeholder.configure(text="No container selected")
                self.cpu_chart_placeholder.pack(expand=True, fill="both", padx=15, pady=15)
                self.cpu_text.pack_forget()
                
                self.memory_chart_placeholder.configure(text="No container selected")
                self.memory_chart_placeholder.pack(expand=True, fill="both", padx=15, pady=15)
                self.memory_text.pack_forget()
                return
                
            # Hide placeholders
            self.cpu_chart_placeholder.pack_forget()
            self.memory_chart_placeholder.pack_forget()
            
            # Show text charts
            self.cpu_text.pack(expand=True, fill="both", padx=15, pady=15)
            self.memory_text.pack(expand=True, fill="both", padx=15, pady=15)
            
            # In a real app with HTML rendering:
            # self.cpu_browser.load_html(self.cpu_plot_html)
            # self.memory_browser.load_html(self.memory_plot_html)
            
            # Display ASCII art charts as a fallback visualization
            filtered_metrics = self.filter_metrics_by_time_range(
                self.container_monitor.get_metrics_history(self.selected_container or "") or []
            )
            
            # CPU visualization
            self.cpu_text.configure(state="normal")
            self.cpu_text.delete("1.0", "end")
            
            if filtered_metrics:
                # Extract CPU data
                timestamps = [datetime.datetime.fromtimestamp(m.get('timestamp', 0)) for m in filtered_metrics]
                cpu_values = [m.get('cpu_percent', 0) for m in filtered_metrics]
                
                # Create ASCII chart for CPU
                chart_width = 50
                chart_height = 8  # Reduced from 10 to make it shorter
                
                # Scale values to chart height
                max_cpu = max(cpu_values) if cpu_values else 100
                if max_cpu < 5:  # If very small values, set a minimum for better visibility
                    max_cpu = 5
                
                # Create chart header
                time_range = self.time_range_var.get()
                cpu_chart = f"CPU Usage Chart ({time_range})\n"
                cpu_chart += f"Container: {self.selected_container[:12] if self.selected_container else 'None'}\n"
                cpu_chart += f"Max: {max_cpu:.1f}%\n"
                cpu_chart += f"Current: {cpu_values[-1] if cpu_values else 0:.1f}%\n\n"
                
                # Create chart
                for y in range(chart_height, 0, -1):
                    threshold = max_cpu * y / chart_height
                    cpu_chart += f"{threshold:5.1f}% |"
                    
                    for x in range(min(len(cpu_values), chart_width)):
                        idx = len(cpu_values) - chart_width + x if len(cpu_values) > chart_width else x
                        if cpu_values[idx] >= threshold:
                            cpu_chart += "█"
                        else:
                            cpu_chart += " "
                    
                    cpu_chart += "|\n"
                
                # Create chart footer
                cpu_chart += "       "
                cpu_chart += "-" * (min(len(cpu_values), chart_width) + 2) + "\n"
                
                # Time scale
                if len(timestamps) > 1:
                    first_time = timestamps[0] if len(timestamps) <= chart_width else timestamps[-chart_width]
                    last_time = timestamps[-1]
                    
                    cpu_chart += f"       {first_time.strftime('%H:%M:%S')}".ljust(chart_width//2 + 8)
                    cpu_chart += f"{last_time.strftime('%H:%M:%S')}\n"
                
                # Add data points count
                cpu_chart += f"\nData points: {len(filtered_metrics)}"
                
                self.cpu_text.insert("1.0", cpu_chart)
            else:
                self.cpu_text.insert("1.0", "No CPU metrics data available for the selected time range.")
                
            self.cpu_text.configure(state="disabled")
            
            # Memory visualization
            self.memory_text.configure(state="normal")
            self.memory_text.delete("1.0", "end")
            
            if filtered_metrics:
                # Extract memory data
                timestamps = [datetime.datetime.fromtimestamp(m.get('timestamp', 0)) for m in filtered_metrics]
                memory_values = [m.get('memory_percent', 0) for m in filtered_metrics]
                memory_usage = [m.get('memory_usage', 0) / (1024*1024) for m in filtered_metrics]  # MB
                
                # Create ASCII chart for memory
                chart_width = 50
                chart_height = 8  # Reduced from 10 to make it shorter
                
                # Scale values to chart height
                max_memory = max(memory_values) if memory_values else 100
                if max_memory < 5:  # If very small values, set a minimum for better visibility
                    max_memory = 5
                
                # Get current memory usage in MB
                current_memory_mb = memory_usage[-1] if memory_usage else 0
                
                # Create chart header
                time_range = self.time_range_var.get()
                memory_chart = f"Memory Usage Chart ({time_range})\n"
                memory_chart += f"Container: {self.selected_container[:12] if self.selected_container else 'None'}\n"
                memory_chart += f"Max: {max_memory:.1f}%\n"
                memory_chart += f"Current: {memory_values[-1] if memory_values else 0:.1f}% ({current_memory_mb:.1f} MB)\n\n"
                
                # Create chart
                for y in range(chart_height, 0, -1):
                    threshold = max_memory * y / chart_height
                    memory_chart += f"{threshold:5.1f}% |"
                    
                    for x in range(min(len(memory_values), chart_width)):
                        idx = len(memory_values) - chart_width + x if len(memory_values) > chart_width else x
                        if memory_values[idx] >= threshold:
                            memory_chart += "█"
                        else:
                            memory_chart += " "
                    
                    memory_chart += "|\n"
                
                # Create chart footer
                memory_chart += "       "
                memory_chart += "-" * (min(len(memory_values), chart_width) + 2) + "\n"
                
                # Time scale
                if len(timestamps) > 1:
                    first_time = timestamps[0] if len(timestamps) <= chart_width else timestamps[-chart_width]
                    last_time = timestamps[-1]
                    
                    memory_chart += f"       {first_time.strftime('%H:%M:%S')}".ljust(chart_width//2 + 8)
                    memory_chart += f"{last_time.strftime('%H:%M:%S')}\n"
                
                # Add data points count
                memory_chart += f"\nData points: {len(filtered_metrics)}"
                
                self.memory_text.insert("1.0", memory_chart)
            else:
                self.memory_text.insert("1.0", "No memory metrics data available for the selected time range.")
                
            self.memory_text.configure(state="disabled")
            
        except Exception as e:
            logger.error(f"Error updating graph UI: {e}")
            self.cpu_chart_placeholder.configure(text=f"Error displaying CPU graph: {e}")
            self.cpu_chart_placeholder.pack(expand=True, fill="both", padx=15, pady=15)
            
            self.memory_chart_placeholder.configure(text=f"Error displaying memory graph: {e}")
            self.memory_chart_placeholder.pack(expand=True, fill="both", padx=15, pady=15)
            
    def filter_metrics_by_time_range(self, metrics: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        '''
        Filter metrics based on selected time range.
        
        Args:
            metrics: List of metrics dictionaries
            
        Returns:
            Filtered metrics list
        '''
        if not metrics:
            return []
            
        # Get current time
        now = time.time()
        
        # Determine time range in seconds
        time_range = self.time_range_var.get()
        if time_range == "Last 5 minutes":
            range_seconds = 5 * 60
        elif time_range == "Last 15 minutes":
            range_seconds = 15 * 60
        elif time_range == "Last hour":
            range_seconds = 60 * 60
        else:  # All
            return metrics
            
        # Filter metrics
        return [m for m in metrics if now - m.get('timestamp', 0) <= range_seconds]
        
    def update_metrics(self, metrics: Dict[str, Dict[str, Any]]):
        '''
        Update metrics data.
        
        Args:
            metrics: Dictionary of container metrics
        '''
        # Store current metrics
        self.current_metrics = metrics
        
        # Refresh graphs if needed
        if self.selected_container and self.selected_container in metrics:
            # Only refresh if graphs are visible
            if self.winfo_ismapped() and self.selected_container:
                self.refresh_graphs()
"""
        else:
            return f"# Mock file content for {file_path}\n# This file is not available in the actual code base."
            
        # For unknown files, return generic content based on file extension
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext == '.conf':
            return "# Configuration file\n# Auto-generated for demo\nsetting1 = value1\nsetting2 = value2\n"
        elif ext == '.json':
            return '{\n  "name": "demo",\n  "version": "1.0.0",\n  "description": "Mock file for demo",\n  "config": {\n    "port": 8080\n  }\n}'
        elif ext == '.js':
            return 'const express = require("express");\nconst app = express();\n\napp.get("/", (req, res) => {\n  res.send("Hello World");\n});\n\napp.listen(3000, () => {\n  console.log("Server started on port 3000");\n});'
        elif ext == '.html':
            return '<!DOCTYPE html>\n<html>\n<head>\n  <title>Demo Page</title>\n</head>\n<body>\n  <h1>Hello World</h1>\n  <p>This is a mock HTML file for the demo.</p>\n</body>\n</html>'
        elif ext == '.css':
            return 'body {\n  font-family: Arial, sans-serif;\n  background-color: #f0f0f0;\n  color: #333;\n}\n\nh1 {\n  color: #0066cc;\n}'
        elif ext == '.py':
            return 'import os\nimport sys\n\ndef main():\n    """Main function."""\n    print("Hello World")\n\nif __name__ == "__main__":\n    main()'
        else:
            return f"# Mock content for {file_path}\n# Generated for demonstration purposes"

    def info(self) -> Dict[str, Any]:
        """
        Get mock Docker system information.
        
        Returns:
            Dictionary with Docker system info
        """
        return {
            'ID': 'MOCK:DOCKIFY:DEMO:MODE',
            'Name': 'dockify-demo',
            'SystemTime': datetime.now().isoformat(),
            'ContainersRunning': len([c for c in self.mock_containers if c['State'] == 'running']),
            'ContainersStopped': len([c for c in self.mock_containers if c['State'] != 'running']),
            'Images': len(self.mock_images),
            'ServerVersion': '23.0.0-demo',
            'OperatingSystem': 'Mock Docker Engine',
            'Architecture': 'x86_64',
            'NCPU': 8,
            'MemTotal': 16 * 1024 * 1024 * 1024,  # 16 GB
            'DockerRootDir': '/var/lib/docker',
            'Driver': 'overlay2',
            'Swarm': {
                'NodeID': '',
                'NodeAddr': '',
                'LocalNodeState': 'inactive'
            },
            'Runtimes': {
                'runc': {
                    'path': 'runc'
                }
            },
            'DefaultRuntime': 'runc',
            'SecurityOptions': [
                'name=seccomp,profile=default'
            ]
        }


# Helper MockContainer class for API compatibility
class MockContainer:
    """Mock container for API compatibility."""
    def __init__(self, client, container_id):
        self.client = client
        self.id = container_id
        self.obj = client.get_container(container_id)
        
    def start(self):
        """Start the container."""
        return self.client.start_container(self.id)
        
    def stop(self):
        """Stop the container."""
        return self.client.stop_container(self.id)
        
    def restart(self):
        """Restart the container."""
        return self.client.restart_container(self.id)
        
    def remove(self, force=False):
        """Remove the container."""
        return self.client.remove_container(self.id, force)
        
    def logs(self, **kwargs):
        """Get container logs."""
        tail = kwargs.get('tail', 100)
        return self.client.get_container_logs(self.id, tail).encode('utf-8')
        
    def stats(self, **kwargs):
        """Get container stats."""
        stats = self.client.get_container_stats(self.id)
        
        # Convert to Docker stats format
        return {
            'read': datetime.now().isoformat(),
            'cpu_stats': {
                'cpu_usage': {
                    'total_usage': 10000000000 * stats['cpu_percent'] / 100.0,
                    'percpu_usage': [2500000000 * stats['cpu_percent'] / 100.0] * 4
                },
                'system_cpu_usage': 10000000000000,
                'online_cpus': 4
            },
            'precpu_stats': {
                'cpu_usage': {
                    'total_usage': 9900000000 * stats['cpu_percent'] / 100.0
                },
                'system_cpu_usage': 9995000000000
            },
            'memory_stats': {
                'usage': stats['memory_usage'],
                'limit': stats['memory_limit']
            },
            'networks': {
                'eth0': {
                    'rx_bytes': stats['network_rx'],
                    'tx_bytes': stats['network_tx']
                }
            }
        }
        
    def exec_run(self, cmd, **kwargs):
        """Run a command in the container."""
        # Handle specific commands
        if cmd.startswith('ls -la '):
            path = cmd[7:]
            files = self.client.get_container_file_tree(self.id, path)
            
            # Format as ls -la output
            output = f"total {len(files)}\n"
            for file in files:
                output += f"{file['permissions']} root root {file['size']} May 9 12:34 {file['name']}\n"
                
            return type('MockExecResult', (), {
                'exit_code': 0,
                'output': output.encode('utf-8')
            })
            
        elif cmd.startswith('cat '):
            path = cmd[4:]
            content = self.client.read_container_file(self.id, path)
            
            return type('MockExecResult', (), {
                'exit_code': 0,
                'output': content.encode('utf-8')
            })
            
        else:
            # Generic response
            return type('MockExecResult', (), {
                'exit_code': 0,
                'output': f"Mock execution of '{cmd}'".encode('utf-8')
            })