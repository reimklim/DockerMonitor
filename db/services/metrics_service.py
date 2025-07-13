"""
Сервис для работы с метриками контейнеров.
"""
import logging
import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import desc, func, and_

from db.models.container_history import ContainerHistory

logger = logging.getLogger('dockify.db.services.metrics')


class MetricsService:
    """Сервис для работы с метриками контейнеров."""
    
    def __init__(self, db_session: Session):
        """
        Инициализировать сервис.
        
        Args:
            db_session: Сессия базы данных
        """
        self.db = db_session
    
    def save_metrics(self, user_id: int, metrics: Dict[str, Dict[str, Any]]) -> bool:
        """
        Сохранить метрики контейнеров.
        
        Args:
            user_id: ID пользователя
            metrics: Словарь с метриками контейнеров
            
        Returns:
            bool: True, если сохранение успешно, иначе False
        """
        try:
            # Создаем записи истории для каждого контейнера
            for container_id, container_metrics in metrics.items():
                history = ContainerHistory.from_metrics(user_id, container_id, container_metrics)
                self.db.add(history)
            
            # Сохраняем изменения
            self.db.commit()
            
            logger.debug(f"Metrics for {len(metrics)} containers saved successfully for user {user_id}")
            return True
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error saving metrics for user {user_id}: {e}")
            return False
    
    def get_container_metrics(self, user_id: int, container_id: str, 
                             start_time: Optional[datetime.datetime] = None,
                             end_time: Optional[datetime.datetime] = None,
                             limit: int = 1000) -> List[ContainerHistory]:
        """
        Получить метрики контейнера.
        
        Args:
            user_id: ID пользователя
            container_id: ID контейнера
            start_time: Начальное время (опционально)
            end_time: Конечное время (опционально)
            limit: Максимальное количество записей (опционально)
            
        Returns:
            List[ContainerHistory]: Список записей истории
        """
        try:
            query = self.db.query(ContainerHistory).filter(
                ContainerHistory.user_id == user_id,
                ContainerHistory.container_id == container_id
            )
            
            if start_time:
                query = query.filter(ContainerHistory.timestamp >= start_time)
            
            if end_time:
                query = query.filter(ContainerHistory.timestamp <= end_time)
            
            # Сортируем по времени (от старых к новым)
            query = query.order_by(ContainerHistory.timestamp)
            
            # Ограничиваем количество записей
            if limit:
                query = query.limit(limit)
            
            return query.all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting metrics for container {container_id}, user {user_id}: {e}")
            return []
    
    def get_latest_metrics(self, user_id: int) -> Dict[str, Dict[str, Any]]:
        """
        Получить последние метрики для всех контейнеров пользователя.
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Dict[str, Dict[str, Any]]: Словарь с последними метриками для каждого контейнера
        """
        try:
            # Подзапрос для получения максимального timestamp для каждого контейнера
            subquery = self.db.query(
                ContainerHistory.container_id,
                func.max(ContainerHistory.timestamp).label('max_timestamp')
            ).filter(
                ContainerHistory.user_id == user_id
            ).group_by(
                ContainerHistory.container_id
            ).subquery()
            
            # Основной запрос для получения записей с максимальным timestamp
            query = self.db.query(ContainerHistory).join(
                subquery,
                and_(
                    ContainerHistory.container_id == subquery.c.container_id,
                    ContainerHistory.timestamp == subquery.c.max_timestamp
                )
            ).filter(
                ContainerHistory.user_id == user_id
            )
            
            # Преобразуем результат в словарь
            result = {}
            for history in query.all():
                result[history.container_id] = history.to_dict()
            
            return result
        except SQLAlchemyError as e:
            logger.error(f"Error getting latest metrics for user {user_id}: {e}")
            return {}
    
    def get_containers_list(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Получить список контейнеров пользователя.
        
        Args:
            user_id: ID пользователя
            
        Returns:
            List[Dict[str, Any]]: Список контейнеров
        """
        try:
            # Подзапрос для получения уникальных контейнеров
            subquery = self.db.query(
                ContainerHistory.container_id,
                ContainerHistory.container_name,
                func.max(ContainerHistory.timestamp).label('last_seen')
            ).filter(
                ContainerHistory.user_id == user_id
            ).group_by(
                ContainerHistory.container_id,
                ContainerHistory.container_name
            )
            
            # Получаем результат
            result = []
            for row in subquery.all():
                result.append({
                    'id': row.container_id,
                    'name': row.container_name,
                    'last_seen': row.last_seen.timestamp() if row.last_seen else None
                })
            
            return result
        except SQLAlchemyError as e:
            logger.error(f"Error getting containers list for user {user_id}: {e}")
            return []
    
    def cleanup_old_metrics(self, user_id: int, days: int = 30) -> int:
        """
        Удалить старые метрики.
        
        Args:
            user_id: ID пользователя
            days: Количество дней, после которых метрики считаются устаревшими
            
        Returns:
            int: Количество удаленных записей
        """
        try:
            # Вычисляем дату, до которой нужно удалить метрики
            cutoff_date = datetime.datetime.utcnow() - datetime.timedelta(days=days)
            
            # Удаляем старые метрики
            result = self.db.query(ContainerHistory).filter(
                ContainerHistory.user_id == user_id,
                ContainerHistory.timestamp < cutoff_date
            ).delete()
            
            # Сохраняем изменения
            self.db.commit()
            
            logger.info(f"Deleted {result} old metrics for user {user_id}")
            return result
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error cleaning up old metrics for user {user_id}: {e}")
            return 0 