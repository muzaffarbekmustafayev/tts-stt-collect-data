from beanie import Document, Link
from datetime import datetime, UTC
from typing import Optional
from pydantic import Field
from enum import Enum
from app.models.user import User
from app.models.sentence import Sentence

class AudioStatus(str, Enum):
    pending = "pending"
    approved = "approved"

class ReceivedAudio(Document):
    user: Link[User]
    sentence: Link[Sentence]
    audio_path: Optional[str] = None
    duration: Optional[float] = None
    status: AudioStatus = AudioStatus.pending
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    class Settings:
        name = "received_audio"
        indexes = [
            [("user", 1), ("sentence", 1)],  # Compound index
            [("status", 1), ("created_at", -1)],  # Compound index
            "audio_path",
        ]
