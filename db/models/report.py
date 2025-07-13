"""
Модель для хранения отчетов.
"""
import datetime
import json
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship

from db.database import Base


class Report(Base):
    """Модель отчета."""
    
    __tablename__ = "reports"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    report_type = Column(String(50), nullable=False)  # excel, csv, pdf, etc.
    file_path = Column(String(500), nullable=True)  # Путь к файлу отчета
    parameters = Column(Text, nullable=True)  # JSON с параметрами отчета
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    is_favorite = Column(Boolean, default=False)
    
    # Отношения с другими таблицами
    user = relationship("User", back_populates="reports")
    
    def set_parameters(self, params: dict) -> None:
        """
        Установить параметры отчета.
        
        Args:
            params: Словарь с параметрами
        """
        self.parameters = json.dumps(params)
    
    def get_parameters(self) -> dict:
        """
        Получить параметры отчета.
        
        Returns:
            dict: Словарь с параметрами
        """
        if not self.parameters:
            return {}
        return json.loads(self.parameters)
    
    def to_dict(self) -> dict:
        """
        Преобразовать отчет в словарь.
        
        Returns:
            dict: Словарь с данными отчета
        """
        result = {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'report_type': self.report_type,
            'file_path': self.file_path,
            'created_at': self.created_at.timestamp(),
            'is_favorite': self.is_favorite
        }
        
        if self.start_date:
            result['start_date'] = self.start_date.timestamp()
        
        if self.end_date:
            result['end_date'] = self.end_date.timestamp()
        
        # Добавляем параметры
        params = self.get_parameters()
        if params:
            result['parameters'] = params
            
        return result
    
    def __repr__(self) -> str:
        """Строковое представление объекта."""
        return f"<Report id={self.id} title={self.title}>" 