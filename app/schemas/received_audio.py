from pydantic import BaseModel, Field, field_serializer
from typing import Optional
from datetime import datetime
from beanie import PydanticObjectId
from app.models.received_audio import AudioStatus

class ReceivedAudioCreate(BaseModel):
    user_id: str
    sentence_id: str

class ReceivedAudioOut(BaseModel):
    id: str = Field(alias="_id")
    user_id: Optional[str] = None
    user_name: Optional[str] = None
    sentence_id: Optional[str] = None
    audio_path: Optional[str] = None
    duration: Optional[float] = None
    sentence: Optional[str] = None
    status: AudioStatus
    created_at: datetime

    model_config = {
        "from_attributes": True,
        "populate_by_name": True
    }

    @field_serializer('id', 'user_id', 'sentence_id')
    def serialize_id(self, value, _info):
        if value:
            return str(value)
        return value
    
    @field_serializer('created_at')
    def serialize_datetime(self, value, _info):
        if isinstance(value, datetime):
            return value.isoformat()
        return value
        
class ReceivedAudioOutPost(BaseModel):
    id: str = Field(alias="_id")
    user_id: Optional[str] = None
    sentence_id: Optional[str] = None
    audio_path: Optional[str] = None
    duration: Optional[float] = None
    status: AudioStatus
    created_at: datetime

    model_config = {
        "from_attributes": True,
        "populate_by_name": True
    }

    @field_serializer('id', 'user_id', 'sentence_id')
    def serialize_id(self, value, _info):
        if value:
            return str(value)
        return value
    
    @field_serializer('created_at')
    def serialize_datetime(self, value, _info):
        if isinstance(value, datetime):
            return value.isoformat()
        return value

class ReceivedAudioOutPut(BaseModel):
    user_id: str
    sentence_id: str
    audio_path: Optional[str] = None
    status: Optional[AudioStatus]

    model_config = {
        "from_attributes": True,
        "populate_by_name": True
    }
