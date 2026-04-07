from pydantic import BaseModel, Field, field_serializer
from typing import Optional
from datetime import datetime
from beanie import PydanticObjectId

class UserCreate(BaseModel):
    name: str
    gender: str
    age: int
    telegram_id: Optional[str] = None
    info: Optional[str] = None

class UserOut(BaseModel):
    id: str = Field(alias="_id")
    telegram_id: Optional[str]
    name: str
    gender: str
    age: int
    info: Optional[str]
    created_at: datetime

    model_config = {
        "from_attributes": True,
        "populate_by_name": True
    }

    @field_serializer('id')
    def serialize_id(self, value, _info):
        return str(value)
    
    @field_serializer('created_at')
    def serialize_datetime(self, value, _info):
        if isinstance(value, datetime):
            return value.isoformat()
        return value
