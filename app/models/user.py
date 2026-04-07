from beanie import Document
from datetime import datetime, UTC
from typing import Optional
from pydantic import Field

class User(Document):
    telegram_id: Optional[str] = Field(None, unique=True)
    name: str
    gender: str
    age: int
    info: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    class Settings:
        name = "users"
        indexes = [
            "telegram_id",
            "created_at",
        ]
