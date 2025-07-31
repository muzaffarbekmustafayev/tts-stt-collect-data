from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from datetime import datetime, timedelta, timezone

from app.models.user import User
from app.schemas.user import UserOut
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
    logger.info(f"User found with user_id: {user_id}")
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
