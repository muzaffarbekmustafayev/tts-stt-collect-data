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
    new_user = User(**user.model_dump())
    if new_user.age < 1 or new_user.age > 120:
        raise HTTPException(status_code=400, detail="Age must be between 1 and 120")
    if new_user.gender.lower() not in ["male", "female"]:
        raise HTTPException(status_code=400, detail="Gender must be either male or female")
    if len(new_user.name) < 3 or len(new_user.name) > 100:
        raise HTTPException(status_code=400, detail="Name must be between 3 and 100 characters")
    if len(new_user.info) > 500:
        raise HTTPException(status_code=400, detail="Info must be less than 500 characters")
    if new_user.telegram_id:
        new_user.telegram_id = new_user.telegram_id.strip()
        if len(new_user.telegram_id) < 5 or len(new_user.telegram_id) > 100:
            raise HTTPException(status_code=400, detail="Telegram ID must be between 5 and 100 characters")
        telegram_ids = await db.execute(select(User.telegram_id))
        if new_user.telegram_id in [u[0] for u in telegram_ids.all()]:
            raise HTTPException(status_code=400, detail="Telegram ID already exists")
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
        user_data.telegram_id = user_data.telegram_id.strip()
        if len(user_data.telegram_id) < 5 or len(user_data.telegram_id) > 100:
            raise HTTPException(status_code=400, detail="Telegram ID must be between 5 and 100 characters")
        telegram_ids = await db.execute(select(User.telegram_id).where(User.id != id))
        if user_data.telegram_id in [u[0] for u in telegram_ids.all()]:
            raise HTTPException(status_code=400, detail="Telegram ID already exists")
        db_user.telegram_id = user_data.telegram_id
    
    await db.commit()
    await db.refresh(db_user)
    logger.info(f"User updated successfully with ID: {db_user.id}")
    return db_user


async def get_user_statistic(user_telegram_id: str, db: AsyncSession) -> tuple[datetime, int, int, int, int]:
    
    sent_count_subq = (
        select(func.count(ReceivedAudio.id))
        .where(ReceivedAudio.user_id == User.id)
        .where(ReceivedAudio.status == AudioStatus.approved)
        .correlate(User)
        .scalar_subquery()
    )

    checked_count_subq = (
        select(func.count(CheckedAudio.id))
        .where(CheckedAudio.checked_by == User.id)
        .where(CheckedAudio.status == AudioStatus.approved)
        .correlate(User)
        .scalar_subquery()
    )

    sent_duration_subq = (
        select(func.sum(ReceivedAudio.duration))
        .where(ReceivedAudio.user_id == User.id)
        .correlate(User)
        .scalar_subquery()
    )

    checked_duration_subq = (
        select(func.sum(ReceivedAudio.duration))
        .select_from(CheckedAudio)
        .join(ReceivedAudio, CheckedAudio.audio_id == ReceivedAudio.id)
        .where(CheckedAudio.checked_by == User.id)
        .correlate(User)
        .scalar_subquery()
    )

    stmt = (
        select(
            sent_count_subq.label("sent_audio_count"),
            checked_count_subq.label("checked_audio_count"),
            sent_duration_subq.label("sent_audio_duration"),
            checked_duration_subq.label("checked_audio_duration"),
            User.created_at
        )
        .where(User.telegram_id == user_telegram_id)
    )
    
    result = await db.execute(stmt)
    row = result.first()

    if not row:
        logger.warning(f"User not found with telegram_id: {user_telegram_id}")
        raise HTTPException(status_code=404, detail="User not found")

    sent_audio_count, checked_audio_count, sent_audio_duration, checked_audio_duration, created_at = row
    regisTime = datetime.now(timezone.utc) - created_at

    return regisTime, sent_audio_count, sent_audio_duration or 0, checked_audio_count, checked_audio_duration or 0


async def delete_user(id: int, db: AsyncSession) -> User:
    """
    Delete a user if they have no associated audio records.
    Checks for both received audio contributions and checked audio records.
    """
    # Get the user first
    user = await get_user_by_userId(id, db)
    logger.info(f"Attempting to delete user: {user.telegram_id} (ID: {id})")

    # Check if user has any received audio records using exists() for efficiency
    from sqlalchemy.sql import exists
    received_audio_exists_query = select(exists().where(ReceivedAudio.user_id == id))
    received_audio_exists = await db.execute(received_audio_exists_query)
    if received_audio_exists.scalar():
        logger.warning(f"Cannot delete user {id}: has received audio records")
        raise HTTPException(
            status_code=400,
            detail="Cannot delete user: user has contributed audio recordings that must be preserved"
        )

    # Check if user has any checked audio records using exists() for efficiency
    checked_audio_exists_query = select(exists().where(CheckedAudio.checked_by == id))
    checked_audio_exists = await db.execute(checked_audio_exists_query)
    if checked_audio_exists.scalar():
        logger.warning(f"Cannot delete user {id}: has checked audio records")
        raise HTTPException(
            status_code=400,
            detail="Cannot delete user: user has reviewed audio recordings that must be preserved"
        )

    # If no related records exist, proceed with deletion
    try:
        await db.delete(user)
        await db.commit()
        logger.info(f"Successfully deleted user: {user.telegram_id} (ID: {id})")
        return user
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to delete user {id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete user")