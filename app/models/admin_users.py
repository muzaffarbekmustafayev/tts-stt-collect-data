from beanie import Document
from datetime import datetime, UTC
from typing import Optional
from pydantic import Field
from enum import Enum

class AdminRole(str, Enum):
    admin = "admin"
    superadmin = "superadmin"
    checker = "checker"

class AdminUser(Document):
    username: str = Field(..., unique=True)
    password: str
    is_active: bool = True
    role: AdminRole = AdminRole.admin
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    class Settings:
        name = "admin_users"
        indexes = [
            "username",
            [("is_active", 1), ("role", 1)],
        ]
