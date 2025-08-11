from typing import Optional, Tuple, Any
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from app.core.logging import get_logger

logger = get_logger("bot_services")

class BotServiceError(Exception):
    """Bot uchun maxsus exception"""
    def __init__(self, message: str, error_type: str = "general"):
        self.message = message
        self.error_type = error_type
        super().__init__(self.message)

def handle_service_exception(func):
    """Service function larni wrapper qilish uchun decorator"""
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except HTTPException as e:
            # HTTPException ni BotServiceError ga o'tkazish
            raise BotServiceError(e.detail, "http_error")
        except Exception as e:
            logger.error(f"Service error in {func.__name__}: {e}")
            raise BotServiceError("Server xatoligi yuz berdi", "server_error")
    return wrapper

# User services uchun wrapper
@handle_service_exception
async def bot_get_user_by_telegramId(telegram_id: str, db: AsyncSession):
    """Bot uchun user topish - exception ni handle qiladi"""
    from app.services.user_service import get_user_by_telegramId
    return await get_user_by_telegramId(telegram_id, db)

@handle_service_exception
async def bot_get_user_by_userId(user_id: int, db: AsyncSession):
    """Bot uchun user topish - exception ni handle qiladi"""
    from app.services.user_service import get_user_by_userId
    return await get_user_by_userId(user_id, db)

# Sentence services uchun wrapper
@handle_service_exception
async def bot_get_available_sentence(user_id: int, sent_audio_count: int, db: AsyncSession):
    """Bot uchun sentence olish - exception ni handle qiladi"""
    from app.services.sentence_service import get_available_sentence
    return await get_available_sentence(user_id, sent_audio_count, db)

# Received audio services uchun wrapper
@handle_service_exception
async def bot_get_audio_for_checking(user_id: int, db: AsyncSession):
    """Bot uchun audio olish - exception ni handle qiladi"""
    from app.services.received_audio_services import get_available_receivedAudio
    return await get_available_receivedAudio(user_id, 0, db)  # check_audio_count ni hisoblash kerak

# Checked audio services uchun wrapper
@handle_service_exception
async def bot_create_checked_audio(audio_id: int, checked_by: int, is_correct: bool, db: AsyncSession):
    """Bot uchun checked audio yaratish - exception ni handle qiladi"""
    from app.services.checked_audio_services import add_checked_audio, update_checked_audio_result_status
    from app.models.received_audio import AudioStatus
    
    # First create the checked audio record
    checked_audio = await add_checked_audio(checked_by, audio_id, db)
    
    # Then update it with the result
    result = await update_checked_audio_result_status(
        checked_audio.id, 
        AudioStatus.approved, 
        is_correct, 
        db
    )
    return result
