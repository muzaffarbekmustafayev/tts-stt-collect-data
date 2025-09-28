from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from datetime import datetime, timedelta, timezone
from sqlalchemy.exc import IntegrityError

from app.models.user import User
from app.schemas.user import UserOut, UserCreate
from app.models.received_audio import ReceivedAudio
from app.models.checked_audio import CheckedAudio
from app.models.received_audio import AudioStatus
from app.config import settings
from fastapi import HTTPException
import logging
logger = logging.getLogger(__name__)

# get user by user id
async def get_user_by_userId(user_id: int, db: AsyncSession) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        logger.warning(f"User not found with ID: {user_id}")
        raise HTTPException(status_code=404, detail="User not found")
    return user

async def get_user_by_telegramId(telegram_id: str, db: AsyncSession) -> User | None:
    result = await db.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()
    if not user:
        logger.warning(f"User not found with telegram_id: {telegram_id}")
        raise HTTPException(status_code=404, detail="User not found")
    logger.info(f"User found with telegram_id: {telegram_id}")
    return user

async def check_user_sent_audio_over_limit(user_id: int, db: AsyncSession) -> int:
    result = await db.execute(select(func.count(ReceivedAudio.id)).where(ReceivedAudio.user_id == user_id))
    return result.scalar_one()

async def check_user_check_audio_limit(user_id: int, db: AsyncSession) -> bool:
    """
      user uchun user_check_audio_limit ni tekshirish
    """
    check_audio_limit = settings.user_check_audio_limit
    if check_audio_limit > 0:
        result = await db.execute(select(func.count(CheckedAudio.id)).where(CheckedAudio.checked_by == user_id))
        return result.scalar_one()
            
    return check_audio_limit

async def create_user(user: UserCreate, db: AsyncSession) -> User:
    print("user", user)
    new_user = User(**user.model_dump())
    if new_user.age < 1 or new_user.age > 120:
        raise HTTPException(status_code=400, detail="Age must be between 1 and 120")
    if new_user.gender.lower() not in ["male", "female"]:
        raise HTTPException(status_code=400, detail="Gender must be either male or female")
    if len(new_user.name) < 3 or len(new_user.name) > 100:
        raise HTTPException(status_code=400, detail="Name must be between 3 and 100 characters")
    if len(new_user.info) > 500:
        raise HTTPException(status_code=400, detail="Info must be less than 500 characters")
    db.add(new_user)
    try:
        await db.commit()
        await db.refresh(new_user)
        logger.info(f"User created successfully with ID: {new_user.id}")
        return new_user
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="User already exists")
    
async def update_user(id: int, user_data: UserCreate, db: AsyncSession) -> User:
    db_user = await get_user_by_userId(id, db)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
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


async def get_user_statistic(user_telegram_id: str, db: AsyncSession) -> tuple[datetime, int, int]:
    
    sent_count_subq = (
        select(func.count(ReceivedAudio.id))
        .where(ReceivedAudio.user_id == User.id)
        .correlate(User)
        .scalar_subquery()
    )

    checked_count_subq = (
        select(func.count(CheckedAudio.id))
        .where(CheckedAudio.checked_by == User.id)
        .correlate(User)
        .scalar_subquery()
    )

    stmt = (
        select(
            sent_count_subq.label("sent_audio_count"),
            checked_count_subq.label("checked_audio_count"),
            User.created_at
        )
        .where(User.telegram_id == user_telegram_id)
    )
    
    result = await db.execute(stmt)
    row = result.first()

    if not row:
        logger.warning(f"User not found with telegram_id: {user_telegram_id}")
        raise HTTPException(status_code=404, detail="User not found")

    sent_audio_count, checked_audio_count, created_at = row
    regisTime = datetime.now(timezone.utc) - created_at

    return regisTime, sent_audio_count, checked_audio_count


async def delete_user(id: int, db: AsyncSession) -> User:
    user = await get_user_by_userId(id, db)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    await db.delete(user)
    await db.commit()
    return user