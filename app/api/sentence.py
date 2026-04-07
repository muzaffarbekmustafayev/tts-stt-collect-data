import csv
import io
from charset_normalizer import from_bytes
from fastapi import APIRouter, Depends, UploadFile, HTTPException
from beanie import PydanticObjectId
from app.models.sentence import Sentence
from app.schemas.sentence import SentenceCreate
from app.core.logging import get_logger
from app.models.received_audio import ReceivedAudio

from app.services.user_service import get_user_by_userId, check_user_sent_audio_over_limit
from app.services.sentence_service import get_available_sentence, get_sentence_by_id
from app.services.admin_user_service import get_current_admin_user

logger = get_logger("api.sentence")
router = APIRouter(prefix="/sentences", tags=["Sentences"])


def serialize_sentence(s: Sentence) -> dict:
    return {
        "id": str(s.id),
        "text": s.text,
        "language": s.language,
        "created_at": s.created_at.isoformat() if s.created_at else None,
    }


@router.post("/", dependencies=[Depends(get_current_admin_user)])
async def create_sentence(sentence: SentenceCreate):
    new_sentence = Sentence(**sentence.model_dump())
    await new_sentence.insert()
    return serialize_sentence(new_sentence)


@router.get("/user/{user_id}")
async def get_user_sentence(user_id: PydanticObjectId):
    user = await get_user_by_userId(user_id)
    sent_audio_count = await check_user_sent_audio_over_limit(user.id)
    sentence = await get_available_sentence(user.id, sent_audio_count)
    return serialize_sentence(sentence)


@router.delete("/{id}", dependencies=[Depends(get_current_admin_user)])
async def delete_sentence_by_id(id: PydanticObjectId):
    sentence = await get_sentence_by_id(id)
    if not sentence:
        raise HTTPException(status_code=404, detail="Sentence not found")

    received_audio = await ReceivedAudio.find_one(ReceivedAudio.sentence.id == id)
    if received_audio:
        raise HTTPException(status_code=400, detail="You can't delete this sentence because it has in received_audio table")

    await sentence.delete()
    return serialize_sentence(sentence)


@router.post("/file", dependencies=[Depends(get_current_admin_user)])
async def create_sentence_by_file(file: UploadFile):
    if file.content_type not in ("text/csv", "application/vnd.ms-excel"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")

    raw_bytes = await file.read()
    result = from_bytes(raw_bytes).best()
    if not result:
        raise HTTPException(status_code=400, detail="Encoding detection failed")

    decoded_content = str(result)
    csv_file = io.StringIO(decoded_content)
    reader = csv.reader(csv_file)

    texts = []
    for row in reader:
        if not row:
            continue
        text = ", ".join(col.strip() for col in row)
        if text:
            texts.append(text)

    if not texts:
        raise HTTPException(status_code=400, detail="CSV file is empty or contains no valid sentences")

    sentences = [Sentence(text=text, language="uz") for text in texts]
    await Sentence.insert_many(sentences)
    return [serialize_sentence(s) for s in sentences]


@router.put("/{id}", dependencies=[Depends(get_current_admin_user)])
async def update_sentence_by_id(id: PydanticObjectId, sentence: SentenceCreate):
    saved = await get_sentence_by_id(id)
    if not saved:
        raise HTTPException(status_code=404, detail="Sentence not found")
    saved.text = sentence.text
    if sentence.language:
        saved.language = sentence.language
    await saved.save()
    return serialize_sentence(saved)


@router.get("/by-id/{id}")
async def get_sentence_by_id_endpoint(id: PydanticObjectId):
    sentence = await get_sentence_by_id(id)
    if not sentence:
        raise HTTPException(status_code=404, detail="Sentence not found")
    return serialize_sentence(sentence)
