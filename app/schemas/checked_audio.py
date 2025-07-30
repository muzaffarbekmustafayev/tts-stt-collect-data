from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class CheckedAudioCreate(BaseModel):
    audio_id: int
    checked_by: int
    is_correct: bool
    comment: Optional[str]

class CheckedAudioOut(CheckedAudioCreate):
    id: int
    audio_id: int
    checked_by: int
    is_correct: bool
    comment: Optional[str]
    checked_at: datetime

    class Config:
        from_attributes = True
