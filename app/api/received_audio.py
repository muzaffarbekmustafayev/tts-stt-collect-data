from sqlalchemy import select
from app.schemas.received_audio import ReceivedAudioCreate, ReceivedAudioOut
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.models.received_audio import ReceivedAudio
from app.core.logging import get_logger
from app.services.user_service import get_user_by_userId
from app.services.sentence_service import get_sentence_by_id
from app.services.received_audio_services import get_audio_by_user_id_and_sentence_id, update_received_audio_path_status
import shutil
import uuid
from pydub import AudioSegment
from pathlib import Path
import os
from datetime import datetime, UTC

logger = get_logger("api.received_audio")
router = APIRouter(prefix="/received-audio", tags=["Received Audio"])
UPLOAD_DIR = "app/audio"

@router.get("/{user_id}", response_model=list[ReceivedAudioOut])
async def get_audio_by_user(user_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ReceivedAudio).where(ReceivedAudio.user_id == user_id))
    audio_list = result.scalars().all()
    logger.info(f"Found {len(audio_list)} audio records for user {user_id}")
    return audio_list

#upload audio va received audio topib update qilish
@router.post("/", response_model=ReceivedAudioOut)
async def create_received_audio(
    user_id: int,
    sentence_id: int,
    file: UploadFile,
    db: AsyncSession = Depends(get_db)
):
    logger.info(f"Audio upload request - user_id: {user_id}, sentence_id: {sentence_id}, filename: {file.filename}")

    try:
        # 1. MIME type tekshirish
        if not file.content_type.startswith("audio/"):
            raise HTTPException(status_code=400, detail="Uploaded file is not an audio file")
        
        # 2. user va sentence aniqlash
        await get_user_by_userId(user_id, db)
        await get_sentence_by_id(sentence_id, db)
       
        # 3. Mavjud audio borligini tekshirish
        received_audio = await get_audio_by_user_id_and_sentence_id(user_id, sentence_id, db)
        
        # 4. Faylni vaqtinchalik saqlash formatlash almashtirish uchun
        ext = Path(file.filename).suffix.lower()
        if not ext:
            raise HTTPException(status_code=400, detail="File extension missing")

        temp_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}{ext}")
        flac_filename = f"{uuid.uuid4()}.flac"
        flac_path = os.path.join(UPLOAD_DIR, flac_filename)

        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        await file.close()

        # 5. Konvertatsiya
        try:
            audio = AudioSegment.from_file(temp_path)
            audio.export(flac_path, format="flac")
        except Exception as e:
            logger.error(f"Audio conversion failed: {e}")
            raise HTTPException(status_code=500, detail="Audio conversion failed")
        finally:
            os.remove(temp_path)


        # 6. received audio qo'shish (oldin mavjudni update qilish)
        await update_received_audio_path_status(received_audio_id=received_audio.id, file_path=flac_path, db=db)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to save audio record")

    return {"status": "ok", "file_path": flac_path, "id": received_audio.id}