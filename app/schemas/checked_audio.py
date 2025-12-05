from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models.checked_audio import AudioStatus

class CheckedAudioCreate(BaseModel):
    audio_id: int
    checked_by: int
    is_correct: bool
    comment: Optional[str] = None
    status: Optional[AudioStatus] = AudioStatus.pending

class SecondCheckUpdate(BaseModel):
    second_check_result: bool

class CheckedAudioOut(CheckedAudioCreate):
    id: int
    audio_id: int
    checked_by: int
    checked_by_name: Optional[str] = None
    is_correct: Optional[bool] = None
    comment: Optional[str]
    checked_at: datetime
    status: AudioStatus
    second_checker_id: Optional[int] = None
    second_checker_name: Optional[str] = None
    second_check_result: Optional[bool] = None
    second_checked_at: Optional[datetime] = None

    class Config:
        from_attributes = True
