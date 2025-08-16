from pydantic import BaseModel
from datetime import datetime

class AdminUserCreate(BaseModel):
    username: str
    password: str
    role: str

class AdminUserOut(BaseModel):
    id: int
    username: str
    is_active: bool
    role: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
