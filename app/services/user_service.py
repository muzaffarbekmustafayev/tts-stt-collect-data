from beanie import PydanticObjectId
from datetime import datetime, timedelta, timezone
UTC = timezone.utc
from typing import Optional

from app.models.user import User
from app.schemas.user import UserOut, UserCreate
from app.models.received_audio import ReceivedAudio, AudioStatus
from app.models.checked_audio import CheckedAudio
from app.config import settings
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)

# get user by user id
async def get_user_by_userId(user_id: str | PydanticObjectId) -> User | None:
    user = await User.get(user_id)
    if not user:
        logger.warning(f"User not found with ID: {user_id}")
        raise HTTPException(status_code=404, detail="User not found")
    return user

async def get_user_by_telegramId(telegram_id: str) -> User | None:
    user = await User.find_one(User.telegram_id == telegram_id)
    if not user:
        logger.warning(f"User not found with telegram_id: {telegram_id}")
        raise HTTPException(status_code=404, detail="User not found")
    logger.info(f"User found with telegram_id: {telegram_id}")
    return user

async def check_user_sent_audio_over_limit(user_id: PydanticObjectId) -> int:
    return await ReceivedAudio.find(ReceivedAudio.user.id == user_id).count()

async def check_user_check_audio_limit(user_id: PydanticObjectId) -> int:
    """
      user uchun user_check_audio_limit ni tekshirish
    """
    check_audio_limit = settings.user_check_audio_limit
    if check_audio_limit > 0:
        return await CheckedAudio.find(CheckedAudio.checked_by.id == user_id).count()
            
    return check_audio_limit

async def create_user(user_data: UserCreate) -> User:
    if user_data.age < 1 or user_data.age > 120:
        raise HTTPException(status_code=400, detail="Age must be between 1 and 120")
    if user_data.gender.lower() not in ["male", "female"]:
        raise HTTPException(status_code=400, detail="Gender must be either male or female")
    if len(user_data.name) < 3 or len(user_data.name) > 100:
        raise HTTPException(status_code=400, detail="Name must be between 3 and 100 characters")
    if user_data.info and len(user_data.info) > 500:
        raise HTTPException(status_code=400, detail="Info must be less than 500 characters")
    
    if user_data.telegram_id:
        user_data.telegram_id = user_data.telegram_id.strip()
        if len(user_data.telegram_id) < 5 or len(user_data.telegram_id) > 100:
            raise HTTPException(status_code=400, detail="Telegram ID must be between 5 and 100 characters")
        
        # Check if telegram_id exists
        existing_user = await User.find_one(User.telegram_id == user_data.telegram_id)
        if existing_user:
            raise HTTPException(status_code=400, detail="Telegram ID already exists")

    new_user = User(**user_data.model_dump())
    await new_user.insert()
    logger.info(f"User created successfully with ID: {new_user.id}")
    return new_user
    
async def update_user(id: str | PydanticObjectId, user_data: UserCreate) -> User:
    db_user = await get_user_by_userId(id)
    
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
        
        # Check if telegram_id exists for other users
        existing_user = await User.find_one(
            User.telegram_id == user_data.telegram_id,
            User.id != db_user.id
        )
        if existing_user:
            raise HTTPException(status_code=400, detail="Telegram ID already exists")
        db_user.telegram_id = user_data.telegram_id
    
    await db_user.save()
    logger.info(f"User updated successfully with ID: {db_user.id}")
    return db_user


async def get_user_statistic(user_telegram_id: str) -> tuple[timedelta, int, float, int, float]:
    user = await User.find_one(User.telegram_id == user_telegram_id)
    if not user:
        logger.warning(f"User not found with telegram_id: {user_telegram_id}")
        raise HTTPException(status_code=404, detail="User not found")

    # Simple count queries - more reliable than aggregation
    sent_audio_count = await ReceivedAudio.find(
        ReceivedAudio.user.id == user.id,
        ReceivedAudio.status == AudioStatus.approved
    ).count()

    checked_audio_count = await CheckedAudio.find(
        CheckedAudio.checked_by.id == user.id,
        CheckedAudio.status == AudioStatus.approved
    ).count()

    # Duration via aggregation
    sent_duration = 0.0
    try:
        sent_pipeline = [
            {"$match": {"user.$id": user.id, "status": "approved"}},
            {"$group": {"_id": None, "total": {"$sum": {"$ifNull": ["$duration", 0]}}}}
        ]
        sent_res = await ReceivedAudio.aggregate(sent_pipeline).to_list()
        sent_duration = sent_res[0]["total"] if sent_res else 0.0
    except Exception as e:
        logger.warning(f"Sent duration aggregation failed: {e}")

    checked_duration = 0.0
    try:
        checked_pipeline = [
            {"$match": {"checked_by.$id": user.id, "status": "approved"}},
            {"$lookup": {"from": "received_audio", "localField": "audio.$id", "foreignField": "_id", "as": "ra"}},
            {"$unwind": {"path": "$ra", "preserveNullAndEmptyArrays": True}},
            {"$group": {"_id": None, "total": {"$sum": {"$ifNull": ["$ra.duration", 0]}}}}
        ]
        checked_res = await CheckedAudio.aggregate(checked_pipeline).to_list()
        checked_duration = checked_res[0]["total"] if checked_res else 0.0
    except Exception as e:
        logger.warning(f"Checked duration aggregation failed: {e}")

    created_at = user.created_at
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=UTC)
    regisTime = datetime.now(UTC) - created_at

    return regisTime, sent_audio_count, sent_duration, checked_audio_count, checked_duration


async def delete_user(id: str | PydanticObjectId) -> User:
    user = await get_user_by_userId(id)
    logger.info(f"Attempting to delete user: {user.telegram_id} (ID: {id})")

    # Check for relations
    received_exists = await ReceivedAudio.find(ReceivedAudio.user.id == user.id).count() > 0
    if received_exists:
        logger.warning(f"Cannot delete user {id}: has received audio records")
        raise HTTPException(
            status_code=400,
            detail="Cannot delete user: user has contributed audio recordings that must be preserved"
        )

    checked_exists = await CheckedAudio.find(CheckedAudio.checked_by.id == user.id).count() > 0
    if checked_exists:
        logger.warning(f"Cannot delete user {id}: has checked audio records")
        raise HTTPException(
            status_code=400,
            detail="Cannot delete user: user has reviewed audio recordings that must be preserved"
        )

    await user.delete()
    logger.info(f"Successfully deleted user: {user.telegram_id} (ID: {id})")
    return user