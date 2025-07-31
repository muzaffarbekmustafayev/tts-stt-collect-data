from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.models.checked_audio import CheckedAudio
from app.schemas.checked_audio import CheckedAudioCreate, CheckedAudioOut
from app.core.logging import get_logger
from app.services.user_service import get_user_by_userId
from app.services.received_audio_services import get_audio_by_id
from app.services.checked_audio_services import checked_audio_and_update

logger = get_logger("api.checked_audio")
router = APIRouter(prefix="/checked-audio", tags=["Checked Audio"])

@router.post("/", response_model=CheckedAudioOut)
async def check_audio(data: CheckedAudioCreate, db: AsyncSession = Depends(get_db)):
    # checked_by, audio_id, is_correct
    # 1. check user
    await get_user_by_userId(data.checked_by, db)
    # 2. check audio_id
    await get_audio_by_id(data.audio_id, db)
    # 3. check if audio is already checked
    result = await checked_audio_and_update(data.checked_by, data.audio_id, data.is_correct, db)
    return result
    

@router.get("/by-audio/{audio_id}", response_model=list[CheckedAudioOut])
async def get_check_by_audio(audio_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(CheckedAudio).where(CheckedAudio.audio_id == audio_id))
    check_list = result.scalars().all()
    logger.info(f"Found {len(check_list)} checked audio records for audio {audio_id}")
    return check_list
