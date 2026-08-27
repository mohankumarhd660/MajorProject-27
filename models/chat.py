from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from models.base import Base


class ChatMessage(Base):
    __tablename__ = "chat_history"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False, index=True)
    thread_id = Column(String(64), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # user | assistant
    content = Column(Text, nullable=False)
    source = Column(String(20), nullable=False, default="ai")  # dataset | ai
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
