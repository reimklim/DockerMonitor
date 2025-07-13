"""
Модель пользователя для аутентификации и авторизации.
"""
import datetime
import bcrypt
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import relationship

from db.database import Base


class User(Base):
    """Модель пользователя."""
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    full_name = Column(String(100), nullable=True)
    password_hash = Column(String(128), nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    # Отношения с другими таблицами
    settings = relationship("UserSettings", back_populates="user", uselist=False)
    reports = relationship("Report", back_populates="user")
    alert_history = relationship("AlertHistory", back_populates="user")
    
    def set_password(self, password: str) -> None:
        """
        Установить хешированный пароль.
        
        Args:
            password: Пароль в открытом виде
        """
        # Генерируем соль и хешируем пароль
        password_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password_bytes, salt)
        self.password_hash = hashed.decode('utf-8')
    
    def check_password(self, password: str) -> bool:
        """
        Проверить пароль.
        
        Args:
            password: Пароль в открытом виде
            
        Returns:
            bool: True, если пароль верный, иначе False
        """
        password_bytes = password.encode('utf-8')
        hashed = self.password_hash.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hashed)
    
    def update_last_login(self) -> None:
        """Обновить время последнего входа."""
        self.last_login = datetime.datetime.utcnow()
    
    def __repr__(self) -> str:
        """Строковое представление объекта."""
        return f"<User {self.username}>" 