from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.models.checked_audio import CheckedAudio
from app.schemas.checked_audio import CheckedAudioCreate, CheckedAudioOut
from app.core.logging import get_logger

logger = get_logger("api.checked_audio")
router = APIRouter(prefix="/checked-audio", tags=["Checked Audio"])

@router.post("/", response_model=CheckedAudioOut)
async def check_audio(data: CheckedAudioCreate, db: AsyncSession = Depends(get_db)):
    new_check = CheckedAudio(**data.model_dump())
    db.add(new_check)
    await db.commit()
    await db.refresh(new_check)
    logger.info(f"Checked audio record created successfully with ID: {new_check.id}")
    return new_check

@router.get("/by-audio/{audio_id}", response_model=list[CheckedAudioOut])
async def get_check_by_audio(audio_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(CheckedAudio).where(CheckedAudio.audio_id == audio_id))
    check_list = result.scalars().all()
    logger.info(f"Found {len(check_list)} checked audio records for audio {audio_id}")
    return check_list
