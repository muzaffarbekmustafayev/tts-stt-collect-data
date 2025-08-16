from sqlalchemy import Column, Integer, String, DateTime, Text
from datetime import datetime, UTC
from app.models.base import Base

class Sentence(Base):
    __tablename__ = "sentences"

    id = Column(Integer, primary_key=True, index=True)
    text = Column(Text, nullable=False)
    language = Column(String, default="uz", nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.now(UTC))
