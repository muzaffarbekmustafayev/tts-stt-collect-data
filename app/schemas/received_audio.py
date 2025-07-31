from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models.received_audio import AudioStatus

class ReceivedAudioCreate(BaseModel):
    user_id: int
    sentence_id: int
    audio_path: Optional[int] = None
    duration: Optional[int] = None
    status: Optional[AudioStatus] = AudioStatus.pending

class ReceivedAudioOut(BaseModel):
    id: int
    user_id: int
    sentence_id: int
    audio_path: Optional[str] = None
    duration: Optional[int] = None
    status: AudioStatus
    created_at: datetime

    class Config:
        from_attributes = True
