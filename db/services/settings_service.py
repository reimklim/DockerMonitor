"""
Сервис для работы с настройками пользователя.
"""
import logging
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from db.models.user_settings import UserSettings

logger = logging.getLogger('dockify.db.services.settings')


class SettingsService:
    """Сервис для работы с настройками пользователя."""
    
    def __init__(self, db_session: Session):
        """
        Инициализировать сервис.
        
        Args:
            db_session: Сессия базы данных
        """
        self.db = db_session
    
    def get_settings(self, user_id: int) -> Optional[UserSettings]:
        """
        Получить настройки пользователя.
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Optional[UserSettings]: Настройки пользователя или None, если не найдены
        """
        try:
            return self.db.query(UserSettings).filter(UserSettings.user_id == user_id).first()
        except SQLAlchemyError as e:
            logger.error(f"Error getting settings for user {user_id}: {e}")
            return None
    
    def get_settings_dict(self, user_id: int) -> Dict[str, Any]:
        """
        Получить настройки пользователя в виде словаря.
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Dict[str, Any]: Словарь с настройками
        """
        settings = self.get_settings(user_id)
        if settings:
            return settings.to_dict()
        return {
            'poll_interval': 5,
            'docker_socket': '/var/run/docker.sock',
            'enable_alerts': True,
            'auto_adjust_interval': True,
            'theme': 'dark',
            'dashboard_layout': {}
        }
    
    def create_settings(self, user_id: int, **kwargs) -> Optional[UserSettings]:
        """
        Создать настройки пользователя.
        
        Args:
            user_id: ID пользователя
            **kwargs: Настройки
            
        Returns:
            Optional[UserSettings]: Созданные настройки или None в случае ошибки
        """
        try:
            # Проверяем, что настройки для этого пользователя еще не существуют
            existing = self.get_settings(user_id)
            if existing:
                logger.warning(f"Settings for user {user_id} already exist")
                return None
            
            # Создаем настройки
            settings = UserSettings(user_id=user_id, **kwargs)
            
            # Добавляем в базу
            self.db.add(settings)
            self.db.commit()
            
            logger.info(f"Settings for user {user_id} created successfully")
            return settings
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error creating settings for user {user_id}: {e}")
            return None
    
    def update_settings(self, user_id: int, **kwargs) -> bool:
        """
        Обновить настройки пользователя.
        
        Args:
            user_id: ID пользователя
            **kwargs: Настройки для обновления
            
        Returns:
            bool: True, если обновление успешно, иначе False
        """
        try:
            settings = self.get_settings(user_id)
            if not settings:
                # Если настройки не существуют, создаем их
                settings = UserSettings(user_id=user_id)
                self.db.add(settings)
            
            # Обновляем поля
            for key, value in kwargs.items():
                if key == 'dashboard_layout' and isinstance(value, dict):
                    settings.set_dashboard_layout(value)
                elif hasattr(settings, key):
                    setattr(settings, key, value)
            
            # Сохраняем изменения
            self.db.commit()
            
            logger.info(f"Settings for user {user_id} updated successfully")
            return True
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error updating settings for user {user_id}: {e}")
            return False
    
    def delete_settings(self, user_id: int) -> bool:
        """
        Удалить настройки пользователя.
        
        Args:
            user_id: ID пользователя
            
        Returns:
            bool: True, если удаление успешно, иначе False
        """
        try:
            settings = self.get_settings(user_id)
            if not settings:
                logger.warning(f"Settings for user {user_id} not found")
                return False
            
            # Удаляем настройки
            self.db.delete(settings)
            self.db.commit()
            
            logger.info(f"Settings for user {user_id} deleted successfully")
            return True
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error deleting settings for user {user_id}: {e}")
            return False 