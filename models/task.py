from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from models.base import Base


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    subject = Column(String(100), nullable=False, index=True)
    difficulty = Column(String(20), nullable=False)
    task_type = Column(String(30), nullable=False)  # learning | quiz | coding
    status = Column(String(20), nullable=False, default="pending")

    payload_json = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
