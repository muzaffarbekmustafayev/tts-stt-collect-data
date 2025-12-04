from sqlalchemy import Column, Integer, ForeignKey, Boolean, DateTime, Text
from datetime import datetime, UTC
from app.models.base import Base
from app.models.received_audio import AudioStatus
from sqlalchemy.dialects.postgresql import ENUM

class CheckedAudio(Base):
    __tablename__ = "checked_audio"

    id = Column(Integer, primary_key=True, index=True)
    audio_id = Column(Integer, ForeignKey("received_audio.id", ondelete="CASCADE"), nullable=False)
    checked_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=False)
    comment = Column(Text, nullable=True)
    is_correct = Column(Boolean, nullable=True)
    status = Column(ENUM(AudioStatus, name='audiostatus'), default=AudioStatus.pending)
    second_checker_id = Column(Integer, ForeignKey("admin_users.id", ondelete="SET NULL"), nullable=True)
    second_check_result = Column(Boolean, nullable=True)
    checked_at = Column(DateTime(timezone=True), default=datetime.now(UTC))
    second_checked_at = Column(DateTime(timezone=True), nullable=True)