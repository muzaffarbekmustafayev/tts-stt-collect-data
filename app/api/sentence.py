import csv
import io
from charset_normalizer import from_bytes
from fastapi import APIRouter, Depends, UploadFile, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.models.sentence import Sentence
from app.schemas.sentence import SentenceCreate, SentenceOut
from app.core.logging import get_logger
from app.models.received_audio import ReceivedAudio

from app.services.user_service import get_user_by_userId, check_user_sent_audio_over_limit
from app.services.sentence_service import get_available_sentence, get_sentence_by_id
from app.services.admin_user_service import get_current_admin_user

logger = get_logger("api.sentence")
router = APIRouter(prefix="/sentences", tags=["Sentences"])

# add sentence
@router.post("/", response_model=SentenceOut, dependencies=[Depends(get_current_admin_user)])
async def create_sentence(sentence: SentenceCreate, db: AsyncSession = Depends(get_db)):
    new_sentence = Sentence(**sentence.model_dump())
    db.add(new_sentence)
    await db.commit()
    await db.refresh(new_sentence)
    return new_sentence

# get user sentence
@router.get("/user/{user_id}", response_model=SentenceOut)
async def get_user_sentence(user_id: int, db: AsyncSession = Depends(get_db)):
    user = await get_user_by_userId(user_id, db)
    sent_audio_count = await check_user_sent_audio_over_limit(user.id, db)
    sentence = await get_available_sentence(user.id, sent_audio_count, db)
    return sentence

# delete sentence
@router.delete("/{id}", response_model=SentenceOut, dependencies=[Depends(get_current_admin_user)])
async def delete_sentence_by_id(id: int, db: AsyncSession = Depends(get_db)):
    sentence = await get_sentence_by_id(id, db)
    if not sentence:
        raise HTTPException(status_code=404, detail="Sentence not found")
    stmt = select(ReceivedAudio).where(ReceivedAudio.sentence_id == id)
    result = await db.execute(stmt)
    received_audio = result.scalar_one_or_none()
    if received_audio:
        raise HTTPException(status_code=400, detail="You can't delete this sentence because it has in received_audio table")
    await db.delete(sentence)
    await db.commit()
    return sentence


# @router.post("/file", response_model=list[SentenceOut], dependencies=[Depends(get_current_admin_user)])
# async def create_sentence_by_file(file: UploadFile, db: AsyncSession = Depends(get_db)):
#     if file.content_type not in ("text/plain", None):
#         raise HTTPException(status_code=400, detail="Only text files are supported")

#     raw_bytes = await file.read()
#     try:
#         content = raw_bytes.decode("utf-8")
#     except UnicodeDecodeError:
#         # fallback for common encodings if needed
#         content = raw_bytes.decode("utf-8", errors="ignore")

#     lines = [line.strip() for line in content.splitlines()]
#     texts = [line for line in lines if line]

#     if not texts:
#         raise HTTPException(status_code=400, detail="The uploaded file is empty or contains no valid lines")

#     sentences = [Sentence(text=text, language="uz") for text in texts]

#     db.add_all(sentences)
#     await db.flush()
#     await db.commit()

#     return sentences


@router.post("/file", response_model=list[SentenceOut], dependencies=[Depends(get_current_admin_user)])
async def create_sentence_by_file(file: UploadFile, db: AsyncSession = Depends(get_db)):
    # faqat csv fayllarni qabul qilish
    if file.content_type not in ("text/csv", "application/vnd.ms-excel"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")

    raw_bytes = await file.read()

    # 🔹 Avtomatik encoding aniqlash
    result = from_bytes(raw_bytes).best()
    if not result:
        raise HTTPException(status_code=400, detail="Encoding detection failed")

    decoded_content = str(result)  # bu yerda to‘g‘ri dekodlangan matn

    csv_file = io.StringIO(decoded_content)
    reader = csv.reader(csv_file)

    texts = []
    for row in reader:
        if not row:
            continue
        # qatordagi ustunlarni qayta birlashtirish
        text = ", ".join(col.strip() for col in row)
        if text:
            texts.append(text)

    if not texts:
        raise HTTPException(status_code=400, detail="CSV file is empty or contains no valid sentences")

    # DB ga yozish
    sentences = [Sentence(text=text, language="uz") for text in texts]

    db.add_all(sentences)
    await db.flush()
    await db.commit()

    return sentences

@router.put("/{id}", response_model=SentenceOut, dependencies=[Depends(get_current_admin_user)])
async def update_sentence_by_id(id: int, sentence: SentenceCreate, db: AsyncSession = Depends(get_db)):
    savedSentence = await get_sentence_by_id(id, db)
    if not savedSentence:
        raise HTTPException(status_code=404, detail="Sentence not found")
    savedSentence.text = sentence.text
    if sentence.language:
        savedSentence.language = sentence.language
    await db.commit()
    await db.refresh(savedSentence)
    return savedSentence


@router.get("/by-id/{id}", response_model=SentenceOut)
async def get_sentence_by_id_endpoint(id: int, db: AsyncSession = Depends(get_db)):
    sentence = await get_sentence_by_id(id, db)
    if not sentence:
        raise HTTPException(status_code=404, detail="Sentence not found")
    return sentence