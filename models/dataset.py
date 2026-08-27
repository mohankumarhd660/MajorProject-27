from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from models.base import Base


class DatasetEntry(Base):
    __tablename__ = "dataset"

    id = Column(Integer, primary_key=True)
    source_file = Column(String(300), nullable=False, index=True)
    entry_type = Column(String(50), nullable=False, index=True)  # intent | qa | coding | text
    tag = Column(String(100), nullable=True, index=True)

    question = Column(Text, nullable=True)
    answer = Column(Text, nullable=True)
    raw_text = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
