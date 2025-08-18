from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException

from app.models.sentence import Sentence
from app.models.received_audio import ReceivedAudio
from app.models.checked_audio import CheckedAudio
from app.schemas.sentence import SentenceOut
from app.config import settings
from app.models.received_audio import AudioStatus

"""
  agar user audio topgan bo'lsa uni checked audioga qo'shish kerak
"""
async def add_checked_audio(user_id: int, audio_id: int, db: AsyncSession) -> CheckedAudio | None:
    """
      oldin mavjud bo'lmasligi kerak
    """
    stmt = (
        select(CheckedAudio)
        .where(CheckedAudio.checked_by == user_id)
        .where(CheckedAudio.audio_id == audio_id)
    )
    result = await db.execute(stmt)
    checked_audio = result.scalar_one_or_none()  
    if checked_audio:
      raise HTTPException(status_code=400, detail="Checked audio already exists")
    
    checked_audio = CheckedAudio(checked_by=user_id, audio_id=audio_id, status=AudioStatus.pending)
    db.add(checked_audio)
    await db.commit()
    await db.refresh(checked_audio)
    return checked_audio

async def update_checked_audio_to_newUser(user_id: int, checked_audio_id: int, db: AsyncSession) -> CheckedAudio | None:
    """
      user_id va created_at update bo'lish kerak
    """
    stmt = (
        select(CheckedAudio)
        .where(CheckedAudio.id == checked_audio_id)
    )
    result = await db.execute(stmt)
    checked_audio = result.scalar_one_or_none()
    if checked_audio:
      checked_audio.checked_by = user_id
      checked_audio.checked_at = datetime.now(timezone.utc)
      await db.commit()
      await db.refresh(checked_audio)
      return checked_audio
    raise HTTPException(status_code=404, detail="Audio not found")
  
async def update_checked_audio_reassign_to_thisUser(checked_audio_id: int, db: AsyncSession) -> CheckedAudio | None:
    """
      created_at update bo'lish kerak
    """
    stmt = (
        select(CheckedAudio)
        .where(CheckedAudio.id == checked_audio_id)
    )
    result = await db.execute(stmt)
    checked_audio = result.scalar_one_or_none()
    if checked_audio:
      checked_audio.checked_at = datetime.now(timezone.utc)
      await db.commit()
      await db.refresh(checked_audio)
      return checked_audio
    raise HTTPException(status_code=404, detail="Audio not found")
    
# oldin pending bo'lgan audio topib, topilmasa 404 qaytarish
async def get_audio_by_user_id_and_sentence_id(user_id: int, sentence_id: int, db: AsyncSession) -> ReceivedAudio | None:
    stmt = (
        select(ReceivedAudio)
        .where(ReceivedAudio.user_id == user_id)
        .where(ReceivedAudio.sentence_id == sentence_id)
        .where(ReceivedAudio.status == AudioStatus.pending)
    )
    result = await db.execute(stmt)
    received_audio = result.scalar_one_or_none()
    if not received_audio:
      raise HTTPException(status_code=404, detail="Audio not found")
    return received_audio


# POST checked result (status va result update qilish)
async def update_checked_audio_result_status(checked_audio_id: int, status: AudioStatus, is_correct: bool, db: AsyncSession) -> CheckedAudio | None:
    stmt = (
        select(CheckedAudio)
        .where(CheckedAudio.id == checked_audio_id)
    )
    result = await db.execute(stmt)
    checked_audio = result.scalar_one_or_none()
    if not checked_audio:
      raise HTTPException(status_code=404, detail="Checked audio not found")
    checked_audio.status = status
    checked_audio.is_correct = is_correct
    await db.commit()
    await db.refresh(checked_audio)
    return checked_audio
  
async def checked_audio_and_update(user_id: int, audio_id: int, is_correct: bool, db: AsyncSession) -> CheckedAudio | None:
    stmt = (
        select(CheckedAudio)
        .where(CheckedAudio.checked_by == user_id)
        .where(CheckedAudio.audio_id == audio_id)
        .where(CheckedAudio.status == AudioStatus.pending)
    )
    result = await db.execute(stmt)
    checked_audio = result.scalar_one_or_none()
    if not checked_audio:
      raise HTTPException(status_code=404, detail="Checked audio not found")
    checked_audio.status = AudioStatus.approved
    checked_audio.is_correct = is_correct
    await db.commit()
    await db.refresh(checked_audio)
    return checked_audio


async def get_checked_audio_by_id(checked_audio_id: int, db: AsyncSession) -> CheckedAudio | None:
    stmt = select(CheckedAudio).where(CheckedAudio.id == checked_audio_id)
    result = await db.execute(stmt)
    checked_audio = result.scalar_one_or_none()
    if not checked_audio:
      raise HTTPException(status_code=404, detail="Checked audio not found")
    return checked_audio