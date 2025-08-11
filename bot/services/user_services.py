from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.core.logging import get_logger
from fastapi import HTTPException
from sqlalchemy import select
from app.schemas.user import UserCreate

logger = get_logger("user_services")

async def get_user_by_telegramId(telegram_id: str, db: AsyncSession) -> User | None:
    result = await db.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()
    return user


async def create_user(user: UserCreate, db: AsyncSession) -> User:
    db_user = User(**user.model_dump())
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

async def update_user(id: int, user_data: UserCreate, db: AsyncSession) -> User:
    db_user = await get_user_by_telegramId(id, db)
    if not db_user:
        return None
    if user_data.age and (user_data.age < 1 or user_data.age > 120):
        raise HTTPException(status_code=400, detail="Age must be between 1 and 120")
    if user_data.gender and user_data.gender.lower() not in ["male", "female"]:
        raise HTTPException(status_code=400, detail="Gender must be either male or female")
    if user_data.name and (len(user_data.name) < 3 or len(user_data.name) > 100):
        raise HTTPException(status_code=400, detail="Name must be between 3 and 100 characters")
    if user_data.info and len(user_data.info) > 500:
        raise HTTPException(status_code=400, detail="Info must be less than 500 characters")
    # Update user fields
    db_user.name = user_data.name
    db_user.gender = user_data.gender
    db_user.age = user_data.age
    if user_data.info:
        db_user.info = user_data.info
    if user_data.telegram_id:
        db_user.telegram_id = user_data.telegram_id
    
    await db.commit()
    await db.refresh(db_user)
    logger.info(f"User updated successfully with ID: {db_user.id}")
    return db_user