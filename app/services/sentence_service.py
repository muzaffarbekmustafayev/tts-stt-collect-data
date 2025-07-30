# app/services/sentence_service.py

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from datetime import datetime, timedelta, timezone

from app.models import Sentence, ReceivedAudio
from app.schemas import SentenceOut
from app.config import settings
from app.models.received_audio import AudioStatus

async def get_available_sentence(user_id: int, db: AsyncSession) -> Sentence | None:
    timeout_time = datetime.now(timezone.utc) - timedelta(minutes=settings.pending_audio_timeout_minutes)

    # subquery: user oldin bu sentence'ni yubormagan bo'lishi kerak
    user_sentences_subq = (
        select(ReceivedAudio.sentence_id)
        .where(ReceivedAudio.user_id == user_id)
    )

    stmt = (
        select(Sentence)
        .where(Sentence.id.not_in(user_sentences_subq))
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
        .limit(1)
    )

    result = await db.execute(stmt)
    return result.scalar_one_or_none()
