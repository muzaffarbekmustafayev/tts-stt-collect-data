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
from app.services.checked_audio_services import update_checked_audio_reassign_to_thisUser, add_checked_audio, update_checked_audio_to_newUser

"""
  agar user sentence olsa uni received audio qo'shish kerak
"""
async def add_received_audio(user_id: int, sentence_id: int, db: AsyncSession) -> ReceivedAudio | None:
    """
      user_id va created_at update bo'lmasligi kerak
    """
    stmt = (
        select(ReceivedAudio)
        .where(ReceivedAudio.user_id == user_id)
        .where(ReceivedAudio.sentence_id == sentence_id)
    )
    result = await db.execute(stmt)
    received_audio = result.scalar_one_or_none()  
    if received_audio:
      raise HTTPException(status_code=400, detail="Audio already exists")
    
    received_audio = ReceivedAudio(user_id=user_id, sentence_id=sentence_id)
    db.add(received_audio)
    await db.commit()
    await db.refresh(received_audio)
    return received_audio

async def get_or_create_received_audio(user_id: int, sentence_id: int, db: AsyncSession) -> ReceivedAudio:
    """
    Mavjud audio'ni topadi yoki yangi yaratadi
    """
    stmt = (
        select(ReceivedAudio)
        .where(ReceivedAudio.user_id == user_id)
        .where(ReceivedAudio.sentence_id == sentence_id)
    )
    result = await db.execute(stmt)
    received_audio = result.scalar_one_or_none()
    
    if received_audio:
        return received_audio
    else:
        # Yangi audio yaratish
        received_audio = ReceivedAudio(user_id=user_id, sentence_id=sentence_id)
        db.add(received_audio)
        await db.commit()
        await db.refresh(received_audio)
        return received_audio

async def update_received_audio_to_newUser(user_id: int, received_audio_id: int, db: AsyncSession) -> ReceivedAudio | None:
    """
      user_id va created_at update bo'lish kerak
    """
    stmt = (
        select(ReceivedAudio)
        .where(ReceivedAudio.id == received_audio_id)
    )
    result = await db.execute(stmt)
    received_audio = result.scalar_one_or_none()
    if received_audio:
      received_audio.user_id = user_id
      received_audio.created_at = datetime.now(timezone.utc)
      await db.commit()
      await db.refresh(received_audio)
      return received_audio
    raise HTTPException(status_code=404, detail="Audio not found")
  
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

# file yuklangandan keyin update qilish (audio_path va status update qilish)
async def update_received_audio_path_status(received_audio_id: int, file_path: str, db: AsyncSession) -> ReceivedAudio | None:
    stmt = (
        select(ReceivedAudio)
        .where(ReceivedAudio.id == received_audio_id)
    )
    result = await db.execute(stmt)
    received_audio = result.scalar_one_or_none()
    if not received_audio:
      raise HTTPException(status_code=404, detail="Audio not found")
    received_audio.audio_path = file_path
    received_audio.status = AudioStatus.pending
    await db.commit()
    await db.refresh(received_audio)
    return received_audio


async def get_available_receivedAudio(user_id: int, check_audio_count: int, db: AsyncSession) -> ReceivedAudio | None:
    timeout_time = datetime.now(timezone.utc) - timedelta(minutes=settings.pending_audio_timeout_minutes)
     # CHECK 1
    """
      user sent audio limitini tekshirish user_sent_audio_limit dan katta bo'lmasligi kerak
      - barchasi approved bo'lgan audio borligini tekshirish
      - pending bo'lgan audio vaqtida o'tganligini tekshirish
    """
    if settings.user_check_audio_limit!=0 and check_audio_count >= settings.user_check_audio_limit:
      # 1.1. user yuborganlar barchasi qabul qilinganmi      
      stmt = (
        select(func.count(CheckedAudio.id))
        .where(CheckedAudio.checked_by == user_id)
        .where(CheckedAudio.status == AudioStatus.approved)
      )
      result = await db.execute(stmt)
      if result.scalar_one() >= settings.user_check_audio_limit:
        raise HTTPException(status_code=400, detail="The user's sending result limit is over, please wait for the next sentence")
      
      # 1.2. user yuborganlar pending bo'lganlar vaqti tugaganmi     
      stmt = (
        select(CheckedAudio)
        .where(CheckedAudio.checked_by == user_id)
        .where(CheckedAudio.status == AudioStatus.pending)
        .where(CheckedAudio.created_at < timeout_time)
        .limit(1)
      )
      result = await db.execute(stmt)
      checked_audio = result.scalar_one_or_none()
      if checked_audio:
        # agar sentence topilsa, create_at update qilish va userga qayta yuborish
        await update_checked_audio_reassign_to_thisUser(checked_audio.id, db)
        return await get_audio_by_id(checked_audio.audio_id, db)
      else:  
        raise HTTPException(status_code=400, detail="The user's sending audio limit is over, please wait for the next sentence")
      
    # subquery: user oldin bu audioni'ni tekshirmagan bo'lishi kerak
    user_audio_checked_subq = (
        select(CheckedAudio.audio_id)
        .where(CheckedAudio.checked_by == user_id)
    )
    
    # subquery 2: audioni'ni shu user yubormagan bo'lishini kerak
    user_audio_sent_subq = (
        select(ReceivedAudio.sentence_id)
        .where(ReceivedAudio.user_id == user_id)
    )

    # CHECK 2
    """
      audio check limitini tekshirish
      - statusi pending yoki approved bo'lgan checked_audio bor bo'lishi kerak
      - statusi pending bo'lgan audio vaqtida o'tgan bo'lishi kerak
    """
    stmt = (
        select(ReceivedAudio)
        .where(
            select(func.count(CheckedAudio.id))
            .where(CheckedAudio.audio_id == ReceivedAudio.id)
            .where(CheckedAudio.checked_by == user_id)
            .where(
                and_(
                    CheckedAudio.status.in_([AudioStatus.pending, AudioStatus.approved]),
                    or_(
                        CheckedAudio.status != AudioStatus.pending,
                        CheckedAudio.created_at > timeout_time
                    )
                )
            )
            .correlate(ReceivedAudio)
            .scalar_subquery() < settings.audio_check_limit
        )
        .where(ReceivedAudio.id.not_in(user_audio_checked_subq))
        .where(ReceivedAudio.sentence_id.not_in(user_audio_sent_subq))
        .limit(1)
    )

    result = await db.execute(stmt)
    received_audio = result.scalar_one_or_none()
    if received_audio:
      # agar audio topilsa, userga yuborishdan oldin uni checked_audioga qo'shish kerak
      await add_checked_audio(user_id, received_audio.id, db)
      return received_audio
    
    # CHECK 3
    """
      agar audio topilmasa
      - status pending va time limit over bo'lganlar
      - user oldin bu audio'ni yubormagan bo'lishi kerak
      - audio userga tegishli bo'lmaslik kerak
    """
    stmt = (
      select(ReceivedAudio, CheckedAudio.id)
      .join(CheckedAudio, ReceivedAudio.id == CheckedAudio.audio_id)
      .where(
          and_(
              CheckedAudio.id.not_in(user_audio_checked_subq),
              CheckedAudio.status == AudioStatus.pending,
              CheckedAudio.created_at < timeout_time,
              ReceivedAudio.user_id != user_id
          )
      )
      .limit(1)
    )
    result = await db.execute(stmt)
    row = result.first()
    if row:
      received_audio, checked_audio_id = row
      if received_audio:
        # agar audio topilsa, user yuborishdan oldin uni checked_audio user_id va created_at update bo'lish kerak
        await update_checked_audio_to_newUser(user_id, checked_audio_id, db) 
        return received_audio
    
    
    # CHECK 4
    # agar audio topilmasa, usha user uzi oldin band qilinganligini tekshirish
    stmt = (
      select(ReceivedAudio, CheckedAudio.id)
      .join(CheckedAudio, ReceivedAudio.id == CheckedAudio.audio_id)
      .where(
          and_(
              CheckedAudio.checked_by == user_id,
              CheckedAudio.status == AudioStatus.pending,
              CheckedAudio.created_at < timeout_time,
              ReceivedAudio.user_id != user_id
          )
      )
      .limit(1)
    )
    result = await db.execute(stmt)
    row = result.first()
    if row:
      received_audio, checked_audio_id = row
      if received_audio:
        # agar audio topilsa, create_at update qilish va userga qayta yuborish
        await update_checked_audio_reassign_to_thisUser(checked_audio_id, db)
      return received_audio
    raise HTTPException(status_code=404, detail="No available audio found")

async def get_audio_by_id(audio_id: int, db: AsyncSession) -> ReceivedAudio | None:
  stmt = select(ReceivedAudio).where(ReceivedAudio.id == audio_id)
  result = await db.execute(stmt)
  received_audio = result.scalar_one_or_none()
  if not received_audio:
    raise HTTPException(status_code=404, detail="Audio not found")
  return received_audio
