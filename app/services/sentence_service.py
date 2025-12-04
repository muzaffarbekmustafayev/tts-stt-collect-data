from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException

from app.models.sentence import Sentence
from app.models.received_audio import ReceivedAudio
from app.schemas.sentence import SentenceOut
from app.config import settings
from app.models.received_audio import AudioStatus
from app.services.received_audio_services import add_received_audio, update_received_audio_to_newUser, update_received_audio_reassign_to_thisUser

async def get_available_sentence(user_id: int, sent_audio_count: int, db: AsyncSession) -> Sentence | None:
    timeout_time = datetime.now(timezone.utc) - timedelta(minutes=settings.pending_audio_timeout_minutes)

    # CHECK 1
    """
      user sent audio limitini tekshirish user_sent_audio_limit dan katta bo'lmasligi kerak
      - barchasi approved bo'lgan audio borligini tekshirish
      - pending bo'lgan audio vaqtida o'tganligini tekshirish
    """
    if sent_audio_count >= settings.user_sent_audio_limit:
      # 1.1. user yuborganlar barchasi qabul qilinganmi      
      stmt = (
        select(func.count(ReceivedAudio.id))
        .where(ReceivedAudio.user_id == user_id)
        .where(ReceivedAudio.status == AudioStatus.approved)
      )
      result = await db.execute(stmt)
      if result.scalar_one() >= settings.user_sent_audio_limit:
        raise HTTPException(status_code=400, detail="The user's sending audio limit is over, please wait for the next sentence")
      
      # 1.2. user yuborganlar pending bo'lganlar vaqti tugaganmi     
      stmt = (
        select(ReceivedAudio)
        .where(ReceivedAudio.user_id == user_id)
        .where(ReceivedAudio.status == AudioStatus.pending)
        .where(ReceivedAudio.created_at < timeout_time)
        .limit(1)
      )
      result = await db.execute(stmt)
      received_audio = result.scalar_one_or_none()
      if received_audio:
        # agar sentence topilsa, create_at update qilish va userga qayta yuborish
        await update_received_audio_reassign_to_thisUser(user_id, received_audio.sentence_id, db)
        return await get_sentence_by_id(received_audio.sentence_id, db)
      else:  
        raise HTTPException(status_code=400, detail="The user's sending audio limit is over, please wait for the next sentence")

    # subquery: user oldin bu sentence'ni yubormagan bo'lishi kerak
    user_sentences_subq = (
        select(ReceivedAudio.sentence_id)
        .where(ReceivedAudio.user_id == user_id)
    )

    # CHECK 2
    """
      sentence limitini tekshirish
      - statusi pending yoki approved bo'lgan audio bor bo'lishi kerak
      - statusi pending bo'lgan audio vaqtida o'tgan bo'lishi kerak
      - user oldin bu sentence'ni yubormagan bo'lishi kerak
    """
    stmt = (
        select(Sentence)
        .where(
            select(func.count(ReceivedAudio.id))
            .where(ReceivedAudio.sentence_id == Sentence.id)
            .where(
                and_(
                    ReceivedAudio.status.in_([AudioStatus.pending, AudioStatus.approved]),
                    or_(
                        ReceivedAudio.status != AudioStatus.pending,
                        ReceivedAudio.created_at > timeout_time
                    )
                )
            )
            .correlate(Sentence)
            .scalar_subquery() < settings.sentence_to_audio_limit
        )
        .where(Sentence.id.not_in(user_sentences_subq))
        .order_by(func.random())
        .limit(1)
    )

    result = await db.execute(stmt)
    sentence = result.scalar_one_or_none()
    if sentence:
      # agar sentence topilsa, user yuborishdan oldin uni received_audio qo'shish kerak
      await add_received_audio(user_id, sentence.id, db)
      return sentence
    
    # CHECK 3
    """
      agar sentence topilmasa
      - status pending va time limit over bo'lganlar
      - user oldin bu sentence'ni yubormagan bo'lishi kerak
    """
    stmt = (
      select(Sentence, ReceivedAudio.id)
      .join(ReceivedAudio, Sentence.id == ReceivedAudio.sentence_id)
      .where(
          and_(
              Sentence.id.not_in(user_sentences_subq),
              ReceivedAudio.status == AudioStatus.pending,
              ReceivedAudio.created_at < timeout_time
          )
      )
      .order_by(func.random())
      .limit(1)
    )
    result = await db.execute(stmt)
    row = result.first()
    if row:
      sentence, received_audio_id = row
      # agar sentence topilsa, user yuborishdan oldin uni received_audio user_id va created_at update bo'lish kerak
      await update_received_audio_to_newUser(user_id, received_audio_id, db)
      return sentence
    
    # CHECK 4
    """
      agar sentence topilmasa, usha user uzi oldin band qilinganligini tekshirish
      - statusi pending bo'lgan audio vaqtida o'tgan bo'lishi kerak
    """
    stmt = (
      select(Sentence)
      .join(ReceivedAudio, Sentence.id == ReceivedAudio.sentence_id)
      .where(
          and_(
              ReceivedAudio.user_id == user_id,
              ReceivedAudio.status == AudioStatus.pending,
              ReceivedAudio.created_at < timeout_time
          )
      )
      .order_by(func.random())
      .limit(1)
    )
    result = await db.execute(stmt)
    sentence = result.scalar_one_or_none()
    if sentence:
      # agar sentence topilsa, create_at update qilish va userga qayta yuborish
      await update_received_audio_reassign_to_thisUser(user_id, sentence.id, db)
      return sentence
    raise HTTPException(status_code=404, detail="No available sentence found")


async def get_sentence_by_id(sentence_id: int, db: AsyncSession) -> Sentence | None:
    stmt = select(Sentence).where(Sentence.id == sentence_id)
    result = await db.execute(stmt)
    sentence = result.scalar_one_or_none()
    if not sentence:
      raise HTTPException(status_code=404, detail="Sentence not found")
    return sentence