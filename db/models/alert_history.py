"""
Модель для хранения истории оповещений.
"""
import datetime
import json
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship

from db.database import Base


class AlertHistory(Base):
    """Модель истории оповещений."""
    
    __tablename__ = "alert_history"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    container_id = Column(String(64), nullable=True, index=True)
    container_name = Column(String(255), nullable=True)
    alert_type = Column(String(50), nullable=False, index=True)
    severity = Column(String(20), nullable=False)  # info, warning, error, critical
    message = Column(String(500), nullable=False)
    details = Column(Text, nullable=True)  # JSON с дополнительными деталями
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    acknowledged = Column(Boolean, default=False)
    acknowledged_at = Column(DateTime, nullable=True)
    
    # Отношения с другими таблицами
    user = relationship("User", back_populates="alert_history")
    
    @classmethod
    def from_alert(cls, user_id: int, alert: dict):
        """
        Создать запись истории из оповещения.
        
        Args:
            user_id: ID пользователя
            alert: Словарь с данными оповещения
            
        Returns:
            AlertHistory: Новый объект истории
        """
        # Извлекаем основные поля
        container_id = alert.get('container_id')
        container_name = alert.get('container_name')
        alert_type = alert.get('type', 'unknown')
        severity = alert.get('severity', 'info')
        message = alert.get('message', 'No message')
        
        # Создаем копию для хранения дополнительных деталей
        details = {k: v for k, v in alert.items() if k not in ['container_id', 'container_name', 'type', 'severity', 'message']}
        
        return cls(
            user_id=user_id,
            container_id=container_id,
            container_name=container_name,
            alert_type=alert_type,
            severity=severity,
            message=message,
            details=json.dumps(details) if details else None
        )
    
    def get_details(self) -> dict:
        """
        Получить дополнительные д��тали из JSON.
        
        Returns:
            dict: Словарь с дополнительными деталями
        """
        if not self.details:
            return {}
        return json.loads(self.details)
    
    def acknowledge(self) -> None:
        """Отметить оповещение как прочитанное."""
        self.acknowledged = True
        self.acknowledged_at = datetime.datetime.utcnow()
    
    def to_dict(self) -> dict:
        """
        Преобразовать запись в словарь.
        
        Returns:
            dict: Словарь с данными оповещения
        """
        result = {
            'id': self.id,
            'container_id': self.container_id,
            'container_name': self.container_name,
            'type': self.alert_type,
            'severity': self.severity,
            'message': self.message,
            'timestamp': self.timestamp.timestamp(),
            'acknowledged': self.acknowledged
        }
        
        if self.acknowledged_at:
            result['acknowledged_at'] = self.acknowledged_at.timestamp()
        
        # Добавляем дополнительные детали
        details = self.get_details()
        if details:
            result.update(details)
            
        return result
    
    def __repr__(self) -> str:
        """Строковое представление объекта."""
        return f"<AlertHistory type={self.alert_type} severity={self.severity} container={self.container_name}>"