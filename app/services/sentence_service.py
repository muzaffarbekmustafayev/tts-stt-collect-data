from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException

from app.models.sentence import Sentence
from app.models.received_audio import ReceivedAudio
from app.schemas.sentence import SentenceOut
from app.config import settings
from app.models.received_audio import AudioStatus
from app.services.received_audio_services import add_received_audio, update_received_audio_to_newUser

async def get_available_sentence(user_id: int, db: AsyncSession) -> Sentence | None:
    timeout_time = datetime.now(timezone.utc) - timedelta(minutes=settings.pending_audio_timeout_minutes)

    # subquery: user oldin bu sentence'ni yubormagan bo'lishi kerak
    user_sentences_subq = (
        select(ReceivedAudio.sentence_id)
        .where(ReceivedAudio.user_id == user_id)
    )

    """
      so'z limitini tekshirish
      - statusi pending yoki approved bo'lgan audio bor bo'lishi kerak
      - statusi pending bo'lgan audio vaqtida o'tgan bo'lishi kerak
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
        .limit(1)
    )

    result = await db.execute(stmt)
    sentence = result.scalar_one_or_none()
    if sentence:
      # agar sentence topilsa, user yuborishdan oldin uni received_audio qo'shish kerak
      await add_received_audio(user_id, sentence.id, db)
      return sentence
    
    """
      agar sentence topilmasa
      - status pending va time limit over bo'lganlar
      - user oldin bu sentence'ni yubormagan bo'lishi kerak
    """
    stmt = (
      select(Sentence)
      .where(
          and_(
              Sentence.id.not_in(user_sentences_subq),
              ReceivedAudio.status == AudioStatus.pending,
              ReceivedAudio.created_at > timeout_time
          )
      )
      .limit(1)
    )
    result = await db.execute(stmt)
    sentence = result.scalar_one_or_none()
    if not sentence:
      raise HTTPException(status_code=404, detail="No available sentence found")
    # agar sentence topilsa, user yuborishdan oldin uni received_audio user_id va created_at update bo'lish kerak
    await update_received_audio_to_newUser(user_id, sentence.id, db)
    return sentence
