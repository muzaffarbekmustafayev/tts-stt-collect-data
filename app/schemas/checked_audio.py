from pydantic import BaseModel, Field, field_serializer
from typing import Optional
from datetime import datetime
from beanie import PydanticObjectId
from app.models.received_audio import AudioStatus

class CheckedAudioCreate(BaseModel):
    audio_id: str
    checked_by: str
    is_correct: bool
    comment: Optional[str] = None
    status: Optional[AudioStatus] = AudioStatus.pending

class SecondCheckUpdate(BaseModel):
    second_check_result: bool

class CheckedAudioOut(BaseModel):
    id: str = Field(alias="_id")
    audio_id: Optional[str] = None
    checked_by: Optional[str] = None
    checked_by_name: Optional[str] = None
    is_correct: Optional[bool] = None
    comment: Optional[str] = None
    checked_at: datetime
    status: AudioStatus
    second_checker_id: Optional[str] = None
    second_checker_name: Optional[str] = None
    second_check_result: Optional[bool] = None
    second_checked_at: Optional[datetime] = None

    model_config = {
        "from_attributes": True,
        "populate_by_name": True
    }

    @field_serializer('id', 'audio_id', 'checked_by', 'second_checker_id')
    def serialize_id(self, value, _info):
        if value:
            return str(value)
        return value
    
    @field_serializer('checked_at', 'second_checked_at')
    def serialize_datetime(self, value, _info):
        if value and isinstance(value, datetime):
            return value.isoformat()
        return value
