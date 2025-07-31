from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException

from app.models.sentence import Sentence
from app.models.received_audio import ReceivedAudio
from app.schemas.sentence import SentenceOut
from app.config import settings
from app.models.received_audio import AudioStatus

"""
  agar user sentence olsa uni received audio qo'shish kerak
"""
async def add_received_audio(user_id: int, sentence_id: int, db: AsyncSession) -> ReceivedAudio | None:
    received_audio = ReceivedAudio(user_id=user_id, sentence_id=sentence_id, status=AudioStatus.pending)
    db.add(received_audio)
    await db.commit()
    await db.refresh(received_audio)
    return received_audio

async def update_received_audio_to_newUser(user_id: int, sentence_id: int, db: AsyncSession) -> ReceivedAudio | None:
    """
      user_id va created_at update bo'lish kerak
    """
    stmt = (
        select(ReceivedAudio)
        .where(ReceivedAudio.user_id == user_id)
        .where(ReceivedAudio.sentence_id == sentence_id)
    )
    result = await db.execute(stmt)
    received_audio = result.scalar_one_or_none()
    if received_audio:
      received_audio.user_id = user_id
      received_audio.created_at = datetime.now(timezone.utc)
      await db.commit()
      await db.refresh(received_audio)
      return received_audio
    
async def update_received_audio_reassign_to_thisUser(user_id: int, sentence_id: int, db: AsyncSession) -> ReceivedAudio | None:
    """
      created_at update bo'lish kerak
    """
    stmt = (
        select(ReceivedAudio)
        .where(ReceivedAudio.user_id == user_id)
        .where(ReceivedAudio.sentence_id == sentence_id)
    )
    result = await db.execute(stmt)
    received_audio = result.scalar_one_or_none()
    if received_audio:
      received_audio.created_at = datetime.now(timezone.utc)
      await db.commit()
      await db.refresh(received_audio)
      return received_audio
