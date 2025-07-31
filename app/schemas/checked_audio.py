from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models.checked_audio import AudioStatus

class CheckedAudioCreate(BaseModel):
    audio_id: int
    checked_by: int
    is_correct: bool
    comment: Optional[str]
    status: Optional[AudioStatus] = AudioStatus.pending

class CheckedAudioOut(CheckedAudioCreate):
    id: int
    audio_id: int
    checked_by: int
    is_correct: bool
    comment: Optional[str]
    checked_at: datetime
    status: AudioStatus

    class Config:
        from_attributes = True
