from beanie import Document, Link
from datetime import datetime, timezone
UTC = timezone.utc
from typing import Optional
from pydantic import Field
from app.models.received_audio import AudioStatus, ReceivedAudio
from app.models.user import User
from app.models.admin_users import AdminUser

class CheckedAudio(Document):
    audio: Link[ReceivedAudio]
    checked_by: Link[User]
    comment: Optional[str] = None
    is_correct: Optional[bool] = None
    status: AudioStatus = AudioStatus.pending
    second_checker: Optional[Link[AdminUser]] = None
    second_check_result: Optional[bool] = None
    checked_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    second_checked_at: Optional[datetime] = None

    class Settings:
        name = "checked_audio"
        indexes = [
            [("checked_by", 1), ("status", 1)],  # Compound index
            [("audio", 1), ("checked_by", 1)],  # Compound index
            [("status", 1), ("checked_at", -1)],  # Compound index
        ]