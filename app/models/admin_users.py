from sqlalchemy import Column, Integer, String, DateTime, Boolean
from app.models.base import Base
from datetime import datetime, UTC
from enum import Enum
from sqlalchemy.dialects.postgresql import ENUM

class AdminRole(str, Enum):
    admin = "admin"
    superadmin = "superadmin"
    checker = "checker"

class AdminUser(Base):
    __tablename__ = "admin_users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    role = Column(ENUM(AdminRole, name='adminrole'), default=AdminRole.admin)
    created_at = Column(DateTime(timezone=True), default=datetime.now(UTC))
    updated_at = Column(DateTime(timezone=True), default=datetime.now(UTC))
    
