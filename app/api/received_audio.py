from sqlalchemy import select
from app.schemas.received_audio import ReceivedAudioCreate, ReceivedAudioOut
from fastapi import APIRouter, UploadFile,  Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.models.received_audio import ReceivedAudio
from app.core.logging import get_logger
from app.services.user_service import get_user_by_userId, check_user_check_audio_limit
from app.services.sentence_service import get_sentence_by_id
from app.services.received_audio_services import get_audio_by_user_id_and_sentence_id, update_received_audio_path_status, get_available_receivedAudio
import shutil
import uuid
from pydub import AudioSegment
from pathlib import Path
import os
from datetime import datetime, UTC

logger = get_logger("api.received_audio")
router = APIRouter(prefix="/received-audio", tags=["Received Audio"])
UPLOAD_DIR = "app/audio"

#upload audio va received audio topib update qilish
@router.post("/", response_model=ReceivedAudioOut)
async def create_received_audio(
    user_id: int,
    sentence_id: int,
    file: UploadFile,
    db: AsyncSession = Depends(get_db)
):
    logger.info(f"Audio upload request - user_id: {user_id}, sentence_id: {sentence_id}, filename: {file.filename}")
    if not user_id or not sentence_id or not file:
        raise HTTPException(status_code=400, detail="Invalid request")
    
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
        if ext == ".flac":
            shutil.move(temp_path, flac_path)
        else:
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


# user id bo'yicha check qilish uchun audio olish
@router.get("/{user_id}", response_model=list[ReceivedAudioOut])
async def get_audio_by_user(user_id: int, db: AsyncSession = Depends(get_db)):
    # 1. user check
    user = await get_user_by_userId(user_id, db)
    # 2. user limit (check_audio_limit) check if limit exists
    check_audio_count = await check_user_check_audio_limit(user.id, db)
    # 3. get an audio with logic 
    received_audio = await get_available_receivedAudio(user_id, check_audio_count, db)
    return received_audio