from beanie import PydanticObjectId
from fastapi import HTTPException
from app.core.logging import get_logger

logger = get_logger("bot_services")


class BotServiceError(Exception):
    def __init__(self, message: str, error_type: str = "general"):
        self.message = message
        self.error_type = error_type
        super().__init__(self.message)


def handle_service_exception(func):
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except HTTPException as e:
            raise BotServiceError(e.detail, "http_error")
        except BotServiceError:
            raise
        except Exception as e:
            logger.error(f"Service error in {func.__name__}: {e}", exc_info=True)
            raise BotServiceError("Server xatoligi yuz berdi", "server_error")
    return wrapper


@handle_service_exception
async def bot_get_available_sentence(user_id: PydanticObjectId, sent_audio_count: int):
    from app.services.sentence_service import get_available_sentence
    return await get_available_sentence(user_id, sent_audio_count)


@handle_service_exception
async def bot_get_audio_for_checking(user_id: PydanticObjectId):
    from app.services.received_audio_services import get_available_receivedAudio
    from app.services.user_service import check_user_check_audio_limit
    check_count = await check_user_check_audio_limit(user_id)
    return await get_available_receivedAudio(user_id, check_count)


@handle_service_exception
async def bot_create_checked_audio(audio_id: PydanticObjectId, checked_by: PydanticObjectId, is_correct: bool):
    """Update existing pending checked_audio record with result."""
    from app.services.checked_audio_services import checked_audio_and_update
    return await checked_audio_and_update(checked_by, audio_id, is_correct)
