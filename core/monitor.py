"""
Metrics collection and monitoring functionality for Docker containers.
"""
import time
import threading
import logging
from typing import Dict, List, Any, Optional, Callable
import psutil
from concurrent.futures import ThreadPoolExecutor, as_completed

from core.docker_client import DockerClient

logger = logging.getLogger('dockify.monitor')

class ContainerMonitor:
    """
    Monitors Docker containers and collects metrics at regular intervals.
    """
    def __init__(self, docker_client: Any, refresh_interval: int = 5):
        """
        Initialize the container monitor.
        
        Args:
            docker_client: The Docker client instance to use
            refresh_interval: Refresh interval in seconds (default: 5)
        """
        self.docker_client = docker_client
        self.refresh_interval = refresh_interval
        self.metrics_history: Dict[str, List[Dict[str, Any]]] = {}
        self.monitors: Dict[str, Dict[str, Any]] = {}
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.callbacks: List[Callable] = []
        
        # Максимальное количество потоков для сбора метрик
        # Используем небольшое значение, чтобы не перегружать Docker API
        self.max_workers = min(10, (psutil.cpu_count() or 2) * 2)
        logger.info(f"Container monitor initialized with {self.max_workers} worker threads")
        
    def start_monitoring(self) -> None:
        """Start the monitoring thread."""
        if self.running:
            return
            
        self.running = True
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()
        logger.info("Container monitoring started")
        
    def stop_monitoring(self) -> None:
        """Stop the monitoring thread."""
        if not self.running:
            return
            
        logger.info("Stopping container monitoring...")
        self.running = False
        
        # Очищаем историю метрик для освобождения памяти
        self.metrics_history.clear()
        self.callbacks.clear()
        
        if self.thread and self.thread.is_alive():
            try:
                # Устанавливаем очень короткий таймаут для завершения потока
                self.thread.join(timeout=0.5)
                if self.thread.is_alive():
                    logger.warning("Container monitoring thread did not terminate gracefully within timeout")
                else:
                    logger.info("Container monitoring stopped successfully")
            except:
                # Игнорируем любые ошибки при попытке завершить поток
                logger.warning("Error while joining monitoring thread")
        
        # Обнуляем ссылку на поток
        self.thread = None
        
    def add_callback(self, callback: Callable) -> None:
        """
        Add a callback function that will be called when metrics are updated.
        
        Args:
            callback: Function to call when metrics are updated
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
            
    def _monitor_loop(self) -> None:
        """Internal monitoring loop that runs in a separate thread."""
        next_update_time = time.time()
        consecutive_long_collections = 0
        
        while self.running:
            # Если флаг running сброшен, немедленно выходим из цикла
            if not self.running:
                break
                
            current_time = time.time()
            
            # Проверяем, пора ли собирать метрики
            if current_time >= next_update_time:
                try:
                    # Если флаг running сброшен, немедленно выходим из цикла
                    if not self.running:
                        break
                        
                    # Запоминаем время начала сбора метрик
                    start_time = time.time()
                    
                    # Собираем метрики
                    metrics = self._collect_metrics()
                    
                    # Если флаг running сброшен, немедленно выходим из цикла
                    if not self.running:
                        break
                        
                    # Запоминаем время окончания сбора метрик
                    end_time = time.time()
                    collection_time = end_time - start_time
                    
                    # Логируем время сбора метрик для отладки
                    if collection_time > self.refresh_interval:
                        logger.warning(f"Metrics collection took longer than refresh interval ({collection_time:.3f} vs {self.refresh_interval} seconds)")
                        consecutive_long_collections += 1
                        
                        # Если сбор метрик стабильно занимает больше времени, чем интервал,
                        # автоматически увеличиваем интервал
                        if consecutive_long_collections >= 3 and self.refresh_interval < collection_time:
                            new_interval = int(collection_time * 1.2)  # Добавляем 20% запаса
                            logger.warning(f"Automatically increasing refresh interval to {new_interval} seconds due to consistent slow metrics collection")
                            self.refresh_interval = new_interval
                    else:
                        consecutive_long_collections = 0
                        logger.debug(f"Metrics collection took {collection_time:.3f} seconds")
                    
                    # Если флаг running сброшен, немедленно выходим из цикла
                    if not self.running:
                        break
                        
                    # Store metrics in history
                    for container_id, container_metrics in metrics.items():
                        if container_id not in self.metrics_history:
                            self.metrics_history[container_id] = []
                        
                        # Keep last 1000 data points (about 1.5 hours at 5-sec intervals)
                        self.metrics_history[container_id].append(container_metrics)
                        if len(self.metrics_history[container_id]) > 1000:
                            self.metrics_history[container_id].pop(0)
                    
                    # Если флаг running сброшен, немедленно выходим из цикла
                    if not self.running:
                        break
                        
                    # Trigger callbacks
                    for callback in self.callbacks:
                        try:
                            callback(metrics)
                        except Exception as e:
                            logger.error(f"Error in monitoring callback: {e}")
                    
                    # Вычисляем время следующего обновления, учитывая точный интервал
                    # Это гарантирует равномерные интервалы, независимо от времени сбора метрик
                    next_update_time = next_update_time + self.refresh_interval
                    
                    # Если следующее обновление уже должно было произойти (сбор метрик занял слишком много времени),
                    # сдвигаем время следующего обновления на текущее время + интервал
                    if next_update_time < time.time():
                        next_update_time = time.time() + self.refresh_interval
                    
                except Exception as e:
                    logger.error(f"Error in monitoring loop: {e}")
                    import traceback
                    logger.error(traceback.format_exc())
                    # В случае ошибки также обновляем время следующего обновления
                    next_update_time = time.time() + self.refresh_interval
            
            # Вычисляем, сколько нужно спать до следующего обновления
            sleep_time = max(0.1, min(0.5, next_update_time - time.time()))
            
            # Спим короткими интервалами, чтобы быстрее реагировать на изменения интервала или остановку
            time.sleep(sleep_time)
    
    def _collect_container_stats(self, container):
        """
        Collect stats for a single container.
        
        Args:
            container: Container dictionary
            
        Returns:
            Tuple of (container_id, metrics_dict) or (container_id, None) if error
        """
        container_id = container['Id']
        container_name = container['Names'][0].lstrip('/') if container['Names'] else 'unknown'
        
        try:
            stats_start = time.time()
            stats = self.docker_client.get_container_stats(container_id)
            stats_end = time.time()
            
            stats_time = stats_end - stats_start
            if stats_time > 0.5:  # Логируем только медленные запросы
                logger.debug(f"Stats collection for container {container_name} took {stats_time:.3f} seconds")
            
            metrics = {
                'id': container_id,
                'name': container_name,
                'status': container['State'],
                'cpu_percent': stats.get('cpu_percent', 0.0),
                'memory_usage': stats.get('memory_usage', 0),
                'memory_percent': stats.get('memory_percent', 0.0),
                'network_rx': stats.get('network_rx', 0),
                'network_tx': stats.get('network_tx', 0),
                'timestamp': time.time()
            }
            return container_id, metrics
        except Exception as e:
            logger.error(f"Error collecting metrics for container {container_id}: {e}")
            return container_id, None

    def _collect_metrics(self) -> Dict[str, Dict[str, Any]]:
        """
        Collect metrics for all containers.
        
        Returns:
            Dictionary with container ID as key and metrics as value
        """
        start_time = time.time()
        logger.debug("Starting metrics collection")
        
        # Получаем список контейнеров
        list_start = time.time()
        containers = self.docker_client.list_containers()
        list_end = time.time()
        logger.debug(f"Container listing took {list_end - list_start:.3f} seconds, found {len(containers)} containers")
        
        metrics = {}
        
        # Используем ThreadPoolExecutor для параллельного сбора метрик
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Запускаем сбор метрик для каждого контейнера в отдельном потоке
            future_to_container = {
                executor.submit(self._collect_container_stats, container): container
                for container in containers
            }
            
            # Собираем результаты по мере их готовности
            for future in as_completed(future_to_container):
                try:
                    container_id, container_metrics = future.result()
                    if container_metrics:  # Проверяем, что метрики были успешно собраны
                        metrics[container_id] = container_metrics
                except Exception as e:
                    logger.error(f"Exception in thread collecting container metrics: {e}")
        
        end_time = time.time()
        total_time = end_time - start_time
        logger.debug(f"Total metrics collection took {total_time:.3f} seconds for {len(containers)} containers")
                
        return metrics
        
    def get_metrics_history(self, container_id: str) -> List[Dict[str, Any]]:
        """
        Get historical metrics for a specific container.
        
        Args:
            container_id: The ID of the container
            
        Returns:
            List of historical metrics
        """
        return self.metrics_history.get(container_id, [])
        
    def get_system_metrics(self) -> Dict[str, Any]:
        """
        Get system-wide metrics.
        
        Returns:
            Dictionary containing system metrics
        """
        return {
            'cpu_percent': psutil.cpu_percent(interval=0.1),
            'memory_percent': psutil.virtual_memory().percent,
            'memory_total': psutil.virtual_memory().total,
            'memory_available': psutil.virtual_memory().available,
            'disk_percent': psutil.disk_usage('/').percent,
            'timestamp': time.time()
        }

    def set_interval(self, interval: int) -> None:
        """
        Set the refresh interval for monitoring.
        
        Args:
            interval: Refresh interval in seconds
        """
        if interval < 1:
            interval = 1  # Минимальный интервал - 1 секунда
            
        logger.info(f"Setting monitoring interval to {interval} seconds (was {self.refresh_interval} seconds)")
        
        # Обновляем интервал
        self.refresh_interval = interval
        
        # Нет необходимости перезапускать мониторинг, так как _monitor_loop
        # теперь проверяет время следующего обновления на каждой итерации