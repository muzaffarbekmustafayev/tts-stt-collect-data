from typing import Optional, Tuple, Any
from beanie import PydanticObjectId
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
async def bot_get_user_by_telegramId(telegram_id: str):
    """Bot uchun user topish - exception ni handle qiladi"""
    from app.services.user_service import get_user_by_telegramId
    return await get_user_by_telegramId(telegram_id)

@handle_service_exception
async def bot_get_user_by_userId(user_id: PydanticObjectId):
    """Bot uchun user topish - exception ni handle qiladi"""
    from app.services.user_service import get_user_by_userId
    return await get_user_by_userId(user_id)

# Sentence services uchun wrapper
@handle_service_exception
async def bot_get_available_sentence(user_id: PydanticObjectId, sent_audio_count: int):
    """Bot uchun sentence olish - exception ni handle qiladi"""
    from app.services.sentence_service import get_available_sentence
    return await get_available_sentence(user_id, sent_audio_count)

# Received audio services uchun wrapper
@handle_service_exception
async def bot_get_audio_for_checking(user_id: PydanticObjectId):
    """Bot uchun audio olish - exception ni handle qiladi"""
    from app.services.received_audio_services import get_available_receivedAudio
    from app.services.user_service import check_user_check_audio_limit
    check_audio_count = await check_user_check_audio_limit(user_id)
    return await get_available_receivedAudio(user_id, check_audio_count)

# Checked audio services uchun wrapper
@handle_service_exception
async def bot_create_checked_audio(audio_id: PydanticObjectId, checked_by: PydanticObjectId, is_correct: bool):
    """Bot uchun checked audio natijasini saqlash"""
    from app.services.checked_audio_services import checked_audio_and_update
    from app.models.received_audio import AudioStatus
    # get_available_receivedAudio allaqachon pending record yaratgan,
    # shuning uchun faqat uni update qilamiz
    return await checked_audio_and_update(checked_by, audio_id, is_correct)
