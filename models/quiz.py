from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from models.base import Base


class QuizAttempt(Base):
    __tablename__ = "tests"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False, index=True)
    task_id = Column(Integer, nullable=True, index=True)

    questions_json = Column(Text, nullable=False)
    answers_json = Column(Text, nullable=False)
    score = Column(Integer, nullable=False, default=0)
    total = Column(Integer, nullable=False, default=0)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class TopicPerformance(Base):
    __tablename__ = "topic_performance"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False, index=True)
    subject = Column(String(100), nullable=False, index=True)
    topic = Column(String(150), nullable=False, index=True)
    correct = Column(Integer, nullable=False, default=0)
    total = Column(Integer, nullable=False, default=0)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
