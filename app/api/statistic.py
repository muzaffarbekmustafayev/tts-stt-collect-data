from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.models.user import User
from sqlalchemy import select, func
from app.core.logging import get_logger
from app.models.sentence import Sentence
from app.models.received_audio import ReceivedAudio
from app.models.checked_audio import CheckedAudio

logger = get_logger("api.statistic")
router = APIRouter(prefix="/statistic", tags=["Statistic"])

  
#statistic
@router.get("/", response_model=dict)
async def get_statistic(db: AsyncSession = Depends(get_db)):
    users = await db.execute(select(func.count(User.id)))
    users = users.scalar()
    sentences = await db.execute(select(func.count(Sentence.id)))
    sentences = sentences.scalar()
    audios = await db.execute(select(func.count(ReceivedAudio.id)))
    audios = audios.scalar()
    checked_audios = await db.execute(select(func.count(CheckedAudio.id)))
    checked_audios = checked_audios.scalar()
    return {
        "users": users,
        "sentences": sentences,
        "audios": audios,
        "checked_audios": checked_audios
    }


 