"""
Сервис для работы с пользователями.
"""
import logging
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from db.models.user import User
from db.models.user_settings import UserSettings

logger = logging.getLogger('dockify.db.services.user')


class UserService:
    """Сервис для работы с пользователями."""
    
    def __init__(self, db_session: Session):
        """
        Инициализировать сервис.
        
        Args:
            db_session: Сессия базы данных
        """
        self.db = db_session
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """
        Получить пользователя по ID.
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Optional[User]: Пользователь или None, если не найден
        """
        try:
            return self.db.query(User).filter(User.id == user_id).first()
        except SQLAlchemyError as e:
            logger.error(f"Error getting user by ID {user_id}: {e}")
            return None
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """
        Получить пользователя по имени пользователя.
        
        Args:
            username: Имя пользователя
            
        Returns:
            Optional[User]: Пользователь или None, если не найден
        """
        try:
            return self.db.query(User).filter(User.username == username).first()
        except SQLAlchemyError as e:
            logger.error(f"Error getting user by username {username}: {e}")
            return None
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Получить пользователя по email.
        
        Args:
            email: Email пользователя
            
        Returns:
            Optional[User]: Пользователь или None, если не найден
        """
        try:
            return self.db.query(User).filter(User.email == email).first()
        except SQLAlchemyError as e:
            logger.error(f"Error getting user by email {email}: {e}")
            return None
    
    def get_all_users(self) -> List[User]:
        """
        Получить всех пользователей.
        
        Returns:
            List[User]: Список пользователей
        """
        try:
            return self.db.query(User).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting all users: {e}")
            return []
    
    def create_user(self, username: str, email: str, password: str, full_name: str = None, is_admin: bool = False) -> Optional[User]:
        """
        Создать нового пользователя.
        
        Args:
            username: Имя пользователя
            email: Email пользователя
            password: Пароль
            full_name: Полное имя (опционально)
            is_admin: Флаг администратора (опционально)
            
        Returns:
            Optional[User]: Созданный пользователь или None в случае ошибки
        """
        try:
            # Проверяем, что пользователь с таким именем или email не существует
            if self.get_user_by_username(username):
                logger.warning(f"User with username {username} already exists")
                return None
            
            if self.get_user_by_email(email):
                logger.warning(f"User with email {email} already exists")
                return None
            
            # Создаем пользователя
            user = User(
                username=username,
                email=email,
                full_name=full_name,
                is_admin=is_admin
            )
            user.set_password(password)
            
            # Добавляем в базу
            self.db.add(user)
            self.db.flush()  # Чтобы получить ID пользователя
            
            # Создаем настройки по умолчанию
            settings = UserSettings(user_id=user.id)
            self.db.add(settings)
            
            # Сохраняем изменения
            self.db.commit()
            
            logger.info(f"User {username} created successfully with ID {user.id}")
            return user
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error creating user {username}: {e}")
            return None
    
    def update_user(self, user_id: int, **kwargs) -> bool:
        """
        Обновить данные пользователя.
        
        Args:
            user_id: ID пользователя
            **kwargs: Поля для обновления
            
        Returns:
            bool: True, если обновление успешно, иначе False
        """
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                logger.warning(f"User with ID {user_id} not found")
                return False
            
            # Обновляем поля
            for key, value in kwargs.items():
                if key == 'password':
                    user.set_password(value)
                elif hasattr(user, key):
                    setattr(user, key, value)
            
            # Сохраняем изменения
            self.db.commit()
            
            logger.info(f"User {user.username} updated successfully")
            return True
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error updating user with ID {user_id}: {e}")
            return False
    
    def delete_user(self, user_id: int) -> bool:
        """
        Удалить пользователя.
        
        Args:
            user_id: ID пользователя
            
        Returns:
            bool: True, если удаление успешно, иначе False
        """
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                logger.warning(f"User with ID {user_id} not found")
                return False
            
            # Удаляем пользователя
            self.db.delete(user)
            self.db.commit()
            
            logger.info(f"User {user.username} deleted successfully")
            return True
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error deleting user with ID {user_id}: {e}")
            return False
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """
        Аутентифицировать пользователя.
        
        Args:
            username: Имя пользователя или email
            password: Пароль
            
        Returns:
            Optional[User]: Пользователь, если аутентификация успешна, иначе None
        """
        try:
            # Ищем пользователя по имени пользователя или email
            user = self.get_user_by_username(username)
            if not user:
                user = self.get_user_by_email(username)
            
            if not user:
                logger.warning(f"User {username} not found")
                return None
            
            # Проверяем пароль
            if not user.check_password(password):
                logger.warning(f"Invalid password for user {username}")
                return None
            
            # Обновляем время последнего входа
            user.update_last_login()
            self.db.commit()
            
            logger.info(f"User {username} authenticated successfully")
            return user
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error authenticating user {username}: {e}")
            return None 