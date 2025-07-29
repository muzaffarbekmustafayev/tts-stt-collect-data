from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ReceivedAudioCreate(BaseModel):
    user_id: int
    sentence_id: int
    audio_path: str
    duration: Optional[int]

class ReceivedAudioOut(BaseModel):
    id: int
    user_id: int
    sentence_id: int
    audio_path: str
    created_at: datetime

    class Config:
        orm_mode = True
