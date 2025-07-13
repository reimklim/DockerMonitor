"""
Модель для хранения истории метрик контейнеров.
"""
import datetime
import json
from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Text
from sqlalchemy.orm import relationship

from db.database import Base


class ContainerHistory(Base):
    """Модель истории метрик контейнера."""
    
    __tablename__ = "container_history"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    container_id = Column(String(64), nullable=False, index=True)
    container_name = Column(String(255), nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    cpu_percent = Column(Float, default=0.0)
    memory_usage = Column(Integer, default=0)
    memory_percent = Column(Float, default=0.0)
    network_rx = Column(Integer, default=0)
    network_tx = Column(Integer, default=0)
    status = Column(String(50), nullable=True)
    metrics_json = Column(Text, nullable=True)  # Дополнительные метрики в JSON
    
    # Отношения с другими таблицами
    user = relationship("User")
    
    @classmethod
    def from_metrics(cls, user_id: int, container_id: str, metrics: dict):
        """
        Создать запись истории из метрик контейнера.
        
        Args:
            user_id: ID пользователя
            container_id: ID контейнера
            metrics: Словарь с метриками
            
        Returns:
            ContainerHistory: Новый объект истории
        """
        # Извлекаем основные метрики
        basic_metrics = {
            'cpu_percent': metrics.get('cpu_percent', 0.0),
            'memory_usage': metrics.get('memory_usage', 0),
            'memory_percent': metrics.get('memory_percent', 0.0),
            'network_rx': metrics.get('network_rx', 0),
            'network_tx': metrics.get('network_tx', 0),
        }
        
        # Создаем копию метрик без основных полей для хранения в JSON
        extra_metrics = {k: v for k, v in metrics.items() if k not in basic_metrics and k not in ['id', 'name', 'status']}
        
        return cls(
            user_id=user_id,
            container_id=container_id,
            container_name=metrics.get('name', 'unknown'),
            status=metrics.get('status', 'unknown'),
            timestamp=datetime.datetime.fromtimestamp(metrics.get('timestamp', datetime.datetime.utcnow().timestamp())),
            metrics_json=json.dumps(extra_metrics) if extra_metrics else None,
            **basic_metrics
        )
    
    def get_extra_metrics(self) -> dict:
        """
        Получить дополнительные метрики из JSON.
        
        Returns:
            dict: Словарь с дополнительными метриками
        """
        if not self.metrics_json:
            return {}
        return json.loads(self.metrics_json)
    
    def to_dict(self) -> dict:
        """
        Преобразовать запись в словарь.
        
        Returns:
            dict: Словарь с метриками
        """
        result = {
            'container_id': self.container_id,
            'container_name': self.container_name,
            'timestamp': self.timestamp.timestamp(),
            'cpu_percent': self.cpu_percent,
            'memory_usage': self.memory_usage,
            'memory_percent': self.memory_percent,
            'network_rx': self.network_rx,
            'network_tx': self.network_tx,
            'status': self.status
        }
        
        # Добавляем дополнительные метрики
        extra = self.get_extra_metrics()
        if extra:
            result.update(extra)
            
        return result
    
    def __repr__(self) -> str:
        """Строковое представление объекта."""
        return f"<ContainerHistory container={self.container_name} timestamp={self.timestamp}>" 