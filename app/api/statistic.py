from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.models.user import User
from sqlalchemy import select, func
from app.core.logging import get_logger
from app.models.sentence import Sentence
from app.models.received_audio import ReceivedAudio
from app.models.checked_audio import CheckedAudio
from app.models.received_audio import AudioStatus
from typing import Optional

logger = get_logger("api.statistic")
router = APIRouter(prefix="/statistic", tags=["Statistic"])

  
#statistic
@router.get("/", response_model=dict)
async def get_statistic(db: AsyncSession = Depends(get_db)):
    users = await db.execute(select(func.count(User.id)))
    users = users.scalar()
    sentences = await db.execute(select(func.count(Sentence.id)))
    sentences = sentences.scalar()
    audios = await db.execute(select(func.count(ReceivedAudio.id)).where(ReceivedAudio.status == AudioStatus.approved))
    audios = audios.scalar()
    checked_audios = await db.execute(select(func.count(CheckedAudio.id)).where(CheckedAudio.status == AudioStatus.approved))
    checked_audios = checked_audios.scalar()
    total_audio_duration = await db.execute(select(func.sum(ReceivedAudio.duration)).where(ReceivedAudio.status == AudioStatus.approved))
    total_audio_duration = total_audio_duration.scalar()
    return {
        "users": users,
        "sentences": sentences,
        "audios": audios,
        "checked_audios": checked_audios,
        "total_audio_duration": int(total_audio_duration)/60 if total_audio_duration else 0
    }


@router.get("/by-users/", response_model=list[dict])
async def get_statistic_by_users(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1),
    name: Optional[str] = Query(None, description="User name bo'yicha qidirish"),
    db: AsyncSession = Depends(get_db)
):
    """
    Har bir user uchun statistika:
    - Nechta audio yuborganligi va ularning soatlari
    - Nechta audio tekshirganligi va ularning soatlari
    - name query orqali userlarni filter qilish mumkin
    """
    # Har bir user uchun yuborilgan audiolar soni
    sent_count_subq = (
        select(
            ReceivedAudio.user_id,
            func.count(ReceivedAudio.id).label("sent_count"),
            func.sum(ReceivedAudio.duration).label("sent_duration_seconds")
        )
        .where(ReceivedAudio.status == AudioStatus.approved)
        .group_by(ReceivedAudio.user_id)
        .subquery()
    )

    pending_audio_count_subq = (
        select(
            ReceivedAudio.user_id,
            func.count(ReceivedAudio.id).label("pending_count")
        )
        .where(ReceivedAudio.status == AudioStatus.pending)
        .group_by(ReceivedAudio.user_id)
        .subquery()
    )
    
    # Har bir user uchun tekshirilgan audiolar soni va ularning durationlari
    checked_count_subq = (
        select(
            CheckedAudio.checked_by,
            func.count(CheckedAudio.id).label("checked_count"),
            func.sum(ReceivedAudio.duration).label("checked_duration_seconds")
        )
        .join(ReceivedAudio, CheckedAudio.audio_id == ReceivedAudio.id)
        .where(CheckedAudio.status == AudioStatus.approved)
        .group_by(CheckedAudio.checked_by)
        .subquery()
    )

    pending_checked_audio_count_subq = (
        select(
            CheckedAudio.checked_by,
            func.count(CheckedAudio.id).label("pending_checked_count")
        )
        .where(CheckedAudio.status == AudioStatus.pending)
        .group_by(CheckedAudio.checked_by)
        .subquery()
    )
    
    # Barcha userlar bilan join qilish
    stmt = (
        select(
            User.id,
            User.name,
            User.telegram_id,
            func.coalesce(sent_count_subq.c.sent_count, 0).label("sent_audio_count"),
            func.coalesce(sent_count_subq.c.sent_duration_seconds, 0).label("sent_duration_seconds"),
            func.coalesce(pending_audio_count_subq.c.pending_count, 0).label("pending_audio_count"),
            func.coalesce(checked_count_subq.c.checked_count, 0).label("checked_audio_count"),
            func.coalesce(checked_count_subq.c.checked_duration_seconds, 0).label("checked_duration_seconds"),
            func.coalesce(pending_checked_audio_count_subq.c.pending_checked_count, 0).label("pending_checked_audio_count")
        )
        .select_from(User)
        .outerjoin(sent_count_subq, User.id == sent_count_subq.c.user_id)
        .outerjoin(checked_count_subq, User.id == checked_count_subq.c.checked_by)
        .outerjoin(pending_audio_count_subq, User.id == pending_audio_count_subq.c.user_id)
        .outerjoin(pending_checked_audio_count_subq, User.id == pending_checked_audio_count_subq.c.checked_by)
    )
    
    # Name bo'yicha filter
    if name:
        stmt = stmt.where(User.name.ilike(f"%{name}%"))
    
    stmt = stmt.order_by(User.id).offset((page - 1) * limit).limit(limit)
    
    result = await db.execute(stmt)
    rows = result.all()
    
    users_statistics = []
    for row in rows:
        user_id, name, telegram_id, sent_count, sent_duration_sec, pending_audio_count, checked_count, checked_duration_sec, pending_checked_audio_count = row
        
        # Sekundlarni minutga aylantirish (60 sekund = 1 minut)
        sent_duration_hours = (sent_duration_sec or 0) / 60
        checked_duration_hours = (checked_duration_sec or 0) / 60
        
        users_statistics.append({
            "user_id": user_id,
            "name": name,
            "telegram_id": telegram_id,
            "sent_audio_count": sent_count or 0,
            "sent_audio_minutes": round(sent_duration_hours, 2),
            "checked_audio_count": checked_count or 0,
            "checked_audio_minutes": round(checked_duration_hours, 2),
            "pending_audio_count": pending_audio_count or 0,
            "pending_checked_audio_count": pending_checked_audio_count or 0
        })
    
    return users_statistics


@router.get("/by-users/audios/", response_model=dict)
async def get_audios_by_users(
    user_id: Optional[int] = Query(None, description="User ID orqali qidirish"),
    telegram_id: Optional[str] = Query(None, description="Telegram ID orqali qidirish"),
    db: AsyncSession = Depends(get_db)
):
    """
    User ID yoki Telegram ID orqali bir userga tegishli yuborgan audiolari (ReceivedAudio) va tekshirgan audiolarini (CheckedAudio) qaytaradi
    """
    # User ID yoki Telegram ID berilganligini tekshirish
    if not user_id and not telegram_id:
        raise HTTPException(
            status_code=400, 
            detail="user_id yoki telegram_id parametrlaridan kamida bittasi berilishi kerak"
        )
    
    # Userni topish
    user = None
    if user_id:
        user_result = await db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail=f"User topilmadi: user_id={user_id}")
    elif telegram_id:
        user_result = await db.execute(select(User).where(User.telegram_id == telegram_id))
        user = user_result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail=f"User topilmadi: telegram_id={telegram_id}")
    
    # Userning yuborgan audiolarini olish
    sent_audios_stmt = (
        select(ReceivedAudio, Sentence.text)
        .join(Sentence, ReceivedAudio.sentence_id == Sentence.id)
        .where(ReceivedAudio.user_id == user.id)
        .where(ReceivedAudio.status == AudioStatus.approved)
        .order_by(ReceivedAudio.created_at.desc())
    )
    sent_audios_result = await db.execute(sent_audios_stmt)
    sent_audios_rows = sent_audios_result.all()
    
    sent_audios = []
    for received_audio, sentence_text in sent_audios_rows:
        sent_audios.append({
            "id": received_audio.id,
            "sentence_id": received_audio.sentence_id,
            "sentence": sentence_text,
            "audio_path": received_audio.audio_path,
            "duration": received_audio.duration,
            "status": received_audio.status.value,
            "created_at": received_audio.created_at.isoformat() if received_audio.created_at else None
        })
    
    # Userning tekshirgan audiolarini olish
    checked_audios_stmt = (
        select(CheckedAudio, ReceivedAudio, Sentence.text)
        .join(ReceivedAudio, CheckedAudio.audio_id == ReceivedAudio.id)
        .join(Sentence, ReceivedAudio.sentence_id == Sentence.id)
        .where(CheckedAudio.checked_by == user.id)
        .where(CheckedAudio.status == AudioStatus.approved)
        .order_by(CheckedAudio.checked_at.desc())
    )
    checked_audios_result = await db.execute(checked_audios_stmt)
    checked_audios_rows = checked_audios_result.all()
    
    checked_audios = []
    for checked_audio, received_audio, sentence_text in checked_audios_rows:
        checked_audios.append({
            "id": checked_audio.id,
            "audio_id": checked_audio.audio_id,
            "sentence_id": received_audio.sentence_id,
            "sentence": sentence_text,
            "audio_path": received_audio.audio_path,
            "duration": received_audio.duration,
            "is_correct": checked_audio.is_correct,
            "comment": checked_audio.comment,
            "status": checked_audio.status.value,
            "checked_at": checked_audio.checked_at.isoformat() if checked_audio.checked_at else None
        })
    
    return {
        "user_id": user.id,
        "name": user.name,
        "telegram_id": user.telegram_id,
        "sent_audios": sent_audios,
        "checked_audios": checked_audios,
        "sent_audios_count": len(sent_audios),
        "checked_audios_count": len(checked_audios)
    }


