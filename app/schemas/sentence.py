from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class SentenceCreate(BaseModel):
    text: str
    language: Optional[str] = "uz"

class SentenceOut(BaseModel):
    id: int
    text: str
    language: str
    created_at: datetime

    class Config:
        from_attributes = True
