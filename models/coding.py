from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from models.base import Base


class CodingProblem(Base):
    __tablename__ = "coding_problems"

    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    difficulty = Column(String(20), nullable=False)
    description = Column(Text, nullable=False)
    starter_code = Column(Text, nullable=True)
    tests_json = Column(Text, nullable=False)
    source_file = Column(String(300), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class Submission(Base):
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False, index=True)
    problem_id = Column(Integer, nullable=False, index=True)

    code = Column(Text, nullable=False)
    language = Column(String(30), nullable=False, default="python")
    status = Column(String(30), nullable=False)  # ran | accepted | failed | error
    output = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
