from flask_login import UserMixin
from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.sql import func

from models.base import Base


class User(UserMixin, Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, index=True)  # student | teacher
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    is_active = Column(Boolean, default=True, nullable=False)
    
    # Firebase integration fields
    email = Column(String(100), unique=True, nullable=True)
    firebase_uid = Column(String(128), unique=True, nullable=True, index=True)

    def get_id(self):
        return str(self.id)
