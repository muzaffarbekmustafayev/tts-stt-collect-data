from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.db.session import get_db
from app.models.sentence import Sentence
from app.schemas.sentence import SentenceCreate, SentenceOut
import random

router = APIRouter(prefix="/sentences", tags=["Sentences"])

@router.post("/", response_model=SentenceOut)
async def create_sentence(sentence: SentenceCreate, db: AsyncSession = Depends(get_db)):
    new_sentence = Sentence(**sentence.model_dump())
    db.add(new_sentence)
    await db.commit()
    await db.refresh(new_sentence)
    return new_sentence

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
