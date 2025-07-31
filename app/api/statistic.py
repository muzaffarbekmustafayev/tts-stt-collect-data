from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.models.user import User
from sqlalchemy import select, func
from app.core.logging import get_logger
from app.models.sentence import Sentence
from app.models.received_audio import ReceivedAudio
from app.models.checked_audio import CheckedAudio
from app.schemas.user import UserOut
from app.schemas.sentence import SentenceOut
from app.schemas.received_audio import ReceivedAudioOut
from app.schemas.checked_audio import CheckedAudioOut


logger = get_logger("api.statistic")
router = APIRouter(prefix="/statistic", tags=["Statistic"])

# get users
# @router.get("/users", response_model=list[UserOut])
# async def get_users(db: AsyncSession = Depends(get_db)):
#     result = await db.execute(select(User))
#     users = result.scalars().all()
#     return users

# #get sentences
# @router.get("/sentences", response_model=list[SentenceOut])
# async def get_sentences(db: AsyncSession = Depends(get_db)):
#     result = await db.execute(select(Sentence))
#     sentences = result.scalars().all()
#     return sentences

# #get audios
# @router.get("/audios", response_model=list[ReceivedAudioOut])
# async def get_audios(db: AsyncSession = Depends(get_db)):
#     result = await db.execute(select(ReceivedAudio))
#     audios = result.scalars().all()
#     return audios

# #get checked audios
# @router.get("/checked-audios", response_model=list[CheckedAudioOut])
# async def get_checked_audios(db: AsyncSession = Depends(get_db)):
#     result = await db.execute(select(CheckedAudio))
#     checked_audios = result.scalars().all()
#     return checked_audios
  
#statistic
@router.get("/statistic", response_model=dict)
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


 