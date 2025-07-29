from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from datetime import datetime, UTC
from app.models.base import Base

class ReceivedAudio(Base):
    __tablename__ = "received_audio"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    sentence_id = Column(Integer, ForeignKey("sentences.id", ondelete="CASCADE"), nullable=False)
    audio_path = Column(String, nullable=False)
    duration = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.now(UTC))
