from beanie import Document
from datetime import datetime, UTC
from typing import Optional
from pydantic import Field

class Sentence(Document):
    text: str
    language: Optional[str] = "uz"
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    class Settings:
        name = "sentences"
        indexes = [
            "created_at",
            "language",
        ]
