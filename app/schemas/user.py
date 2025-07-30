from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class UserCreate(BaseModel):
    name: str
    gender: str
    age: int
    telegram_id: Optional[str] = None
    info: Optional[str] = None

class UserOut(BaseModel):
    id: int
    telegram_id: Optional[str]
    name: str
    gender: str
    age: int
    info: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
