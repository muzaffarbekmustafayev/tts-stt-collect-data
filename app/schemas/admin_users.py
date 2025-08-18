from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class AdminUserCreate(BaseModel):
    username: str
    password: str
    is_active: Optional[bool] = True
    role: Optional[str] = "admin"

class AdminUserOut(BaseModel):
    id: int
    username: str
    is_active: Optional[bool] = True
    role: Optional[str] = "admin"
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
