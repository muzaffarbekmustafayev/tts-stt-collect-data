from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class UserCreate(BaseModel):
    telegram_id: str
    name: str
    gender: str
    age: str
    info: Optional[str]

class UserOut(BaseModel):
    id: int
    telegram_id: str
    name: str
    gender: str
    age: str
    info: Optional[str]
    created_at: datetime

    class Config:
        orm_mode = True
