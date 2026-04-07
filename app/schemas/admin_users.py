from pydantic import BaseModel, Field, field_serializer
from datetime import datetime
from typing import Optional
from beanie import PydanticObjectId

class AdminUserCreate(BaseModel):
    username: str
    password: str
    is_active: Optional[bool] = True
    role: Optional[str] = "admin"

class AdminUserUpdate(BaseModel):
    username: str
    password: Optional[str] = None
    is_active: Optional[bool] = True
    role: Optional[str] = "admin"

class AdminUserOut(BaseModel):
    id: str = Field(alias="_id")
    username: str
    is_active: Optional[bool] = True
    role: Optional[str] = "admin"
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
        "populate_by_name": True
    }

    @field_serializer('id')
    def serialize_id(self, value, _info):
        return str(value)
    
    @field_serializer('created_at', 'updated_at')
    def serialize_datetime(self, value, _info):
        if isinstance(value, datetime):
            return value.isoformat()
        return value
