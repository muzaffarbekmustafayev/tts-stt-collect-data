from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.db.session import get_db
from app.models.sentence import Sentence
from app.schemas.sentence import SentenceCreate, SentenceOut
from app.core.logging import get_logger
import random
from app.services.user_service import get_user_by_userId, check_user_sent_audio_over_limit
from app.services.sentence_service import get_available_sentence

logger = get_logger("api.sentence")
router = APIRouter(prefix="/sentences", tags=["Sentences"])

# add sentence
@router.post("/", response_model=SentenceOut)
async def create_sentence(sentence: SentenceCreate, db: AsyncSession = Depends(get_db)):
    new_sentence = Sentence(**sentence.model_dump())
    db.add(new_sentence)
    await db.commit()
    await db.refresh(new_sentence)
    return new_sentence

# get random sentence
@router.get("/random", response_model=SentenceOut)
async def get_random_sentence(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(func.count()).select_from(Sentence))
    total = result.scalar()
    if total == 0:
        raise HTTPException(status_code=404, detail="No sentences found")

    random_offset = random.randint(0, total - 1)
    result = await db.execute(select(Sentence).offset(random_offset).limit(1))
    sentence = result.scalar_one()
    return sentence

# get user sentence
@router.get("/user/{user_id}", response_model=SentenceOut)
async def get_user_sentence(user_id: int, db: AsyncSession = Depends(get_db)):
    user = await get_user_by_userId(user_id, db)
    await check_user_sent_audio_over_limit(user.id, db)
    sentence = await get_available_sentence(user.id, db)
    return sentence
