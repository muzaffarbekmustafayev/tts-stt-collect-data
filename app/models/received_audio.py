from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Float
from datetime import datetime, UTC
from app.models.base import Base
from enum import Enum
from sqlalchemy.dialects.postgresql import ENUM

class AudioStatus(str, Enum):
    pending = "pending"
    approved = "approved"

class ReceivedAudio(Base):
    __tablename__ = "received_audio"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    sentence_id = Column(Integer, ForeignKey("sentences.id", ondelete="CASCADE"), nullable=False)
    audio_path = Column(String, nullable=True)
    duration = Column(Float, nullable=True)
    status = Column(ENUM(AudioStatus, name='audiostatus'), default=AudioStatus.pending)
    created_at = Column(DateTime(timezone=True), default=datetime.now(UTC))
