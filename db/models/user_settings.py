"""
Модель для хранения пользовательских настроек.
"""
import datetime
import json
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship

from db.database import Base


class UserSettings(Base):
    """Модель настроек пользователя."""
    
    __tablename__ = "user_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    poll_interval = Column(Integer, default=5)
    docker_socket = Column(String(255), default="/var/run/docker.sock")
    enable_alerts = Column(Boolean, default=True)
    auto_adjust_interval = Column(Boolean, default=True)
    theme = Column(String(50), default="dark")
    dashboard_layout = Column(Text, nullable=True)  # JSON строка с настройками макета
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # Отношения с другими таблицами
    user = relationship("User", back_populates="settings")
    
    def set_dashboard_layout(self, layout_dict: dict) -> None:
        """
        Установить настройки макета дашборда.
        
        Args:
            layout_dict: Словарь с настройками макета
        """
        self.dashboard_layout = json.dumps(layout_dict)
    
    def get_dashboard_layout(self) -> dict:
        """
        Получить настройки макета дашборда.
        
        Returns:
            dict: Словарь с настройками макета
        """
        if not self.dashboard_layout:
            return {}
        return json.loads(self.dashboard_layout)
    
    def to_dict(self) -> dict:
        """
        Преобразовать настройки в словарь.
        
        Returns:
            dict: Словарь с настройками
        """
        return {
            'poll_interval': self.poll_interval,
            'docker_socket': self.docker_socket,
            'enable_alerts': self.enable_alerts,
            'auto_adjust_interval': self.auto_adjust_interval,
            'theme': self.theme,
            'dashboard_layout': self.get_dashboard_layout()
        }
    
    def __repr__(self) -> str:
        """Строковое представление объекта."""
        return f"<UserSettings user_id={self.user_id}>" 