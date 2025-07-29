from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.models.received_audio import ReceivedAudio
from app.schemas.received_audio import ReceivedAudioCreate, ReceivedAudioOut

router = APIRouter(prefix="/received-audio", tags=["Received Audio"])

@router.post("/", response_model=ReceivedAudioOut)
async def create_received_audio(data: ReceivedAudioCreate, db: AsyncSession = Depends(get_db)):
    new_audio = ReceivedAudio(**data.model_dump())
    db.add(new_audio)
    await db.commit()
    await db.refresh(new_audio)
    return new_audio

@router.get("/{user_id}", response_model=list[ReceivedAudioOut])
async def get_audio_by_user(user_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ReceivedAudio).where(ReceivedAudio.user_id == user_id))
    return result.scalars().all()
