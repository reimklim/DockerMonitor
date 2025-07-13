"""
Сервис для работы с отчетами.
"""
import datetime
import logging
from typing import List, Optional, Dict, Any

from sqlalchemy.orm import Session
from sqlalchemy import desc

from db.models.report import Report

logger = logging.getLogger('dockify.db.services.report_service')

class ReportService:
    """Сервис для работы с отчетами."""
    
    def __init__(self, db_session: Session):
        """
        Инициализировать сервис.
        
        Args:
            db_session: Сессия базы данных
        """
        self.db = db_session
    
    def create_report(self, user_id: int, title: str, report_type: str, 
                     file_path: str, start_date: datetime.datetime, 
                     end_date: datetime.datetime, description: str = None,
                     parameters: Dict[str, Any] = None) -> Report:
        """
        Создать новый отчет.
        
        Args:
            user_id: ID пользователя
            title: Название отчета
            report_type: Тип отчета (excel, csv)
            file_path: Путь к файлу отчета
            start_date: Начальная дата отчета
            end_date: Конечная дата отчета
            description: Описание отчета
            parameters: Параметры отчета
            
        Returns:
            Report: Созданный отчет
        """
        try:
            report = Report(
                user_id=user_id,
                title=title,
                report_type=report_type,
                file_path=file_path,
                start_date=start_date,
                end_date=end_date,
                description=description
            )
            
            if parameters:
                report.set_parameters(parameters)
            
            self.db.add(report)
            self.db.commit()
            self.db.refresh(report)
            
            logger.info(f"Created report {report.id} for user {user_id}")
            return report
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating report: {e}")
            raise
    
    def get_reports_by_user(self, user_id: int, limit: int = 10) -> List[Report]:
        """
        Получить отчеты пользователя.
        
        Args:
            user_id: ID пользователя
            limit: Максимальное количество отчетов
            
        Returns:
            List[Report]: Список отчетов
        """
        try:
            reports = self.db.query(Report)\
                .filter(Report.user_id == user_id)\
                .order_by(desc(Report.created_at))\
                .limit(limit)\
                .all()
            
            return reports
        except Exception as e:
            logger.error(f"Error getting reports for user {user_id}: {e}")
            return []
    
    def get_report_by_id(self, report_id: int) -> Optional[Report]:
        """
        Получить отчет по ID.
        
        Args:
            report_id: ID отчета
            
        Returns:
            Optional[Report]: Отчет или None, если отчет не найден
        """
        try:
            return self.db.query(Report).filter(Report.id == report_id).first()
        except Exception as e:
            logger.error(f"Error getting report {report_id}: {e}")
            return None
    
    def delete_report(self, report_id: int) -> bool:
        """
        Удалить отчет.
        
        Args:
            report_id: ID отчета
            
        Returns:
            bool: True, если отчет успешно удален
        """
        try:
            report = self.get_report_by_id(report_id)
            if report:
                self.db.delete(report)
                self.db.commit()
                logger.info(f"Deleted report {report_id}")
                return True
            return False
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting report {report_id}: {e}")
            return False
    
    def update_report(self, report_id: int, **kwargs) -> Optional[Report]:
        """
        Обновить отчет.
        
        Args:
            report_id: ID отчета
            **kwargs: Поля для обновления
            
        Returns:
            Optional[Report]: Обновленный отчет или None, если отчет не найден
        """
        try:
            report = self.get_report_by_id(report_id)
            if not report:
                return None
                
            for key, value in kwargs.items():
                if hasattr(report, key):
                    setattr(report, key, value)
            
            self.db.commit()
            self.db.refresh(report)
            
            logger.info(f"Updated report {report_id}")
            return report
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating report {report_id}: {e}")
            return None
    
    def toggle_favorite(self, report_id: int) -> Optional[bool]:
        """
        Переключить флаг избранного отчета.
        
        Args:
            report_id: ID отчета
            
        Returns:
            Optional[bool]: Новое значение флага или None, если отчет не найден
        """
        try:
            report = self.get_report_by_id(report_id)
            if not report:
                return None
                
            report.is_favorite = not report.is_favorite
            self.db.commit()
            
            logger.info(f"Toggled favorite for report {report_id} to {report.is_favorite}")
            return report.is_favorite
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error toggling favorite for report {report_id}: {e}")
            return None 