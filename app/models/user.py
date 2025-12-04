from sqlalchemy import Column, Integer, String, DateTime, Text
from app.models.base import Base
from datetime import datetime, UTC

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(String, unique=True, index=True, nullable=True)
    name = Column(String, nullable=False)
    gender = Column(String, nullable=False)
    age = Column(Integer, nullable=False)
    info = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.now(UTC))
