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
        # 1. user aniqlash
        user = await get_user_by_userId(user_id, db)
        # 2. sentence aniqlash
        sentence = await get_sentence_by_id(sentence_id, db)
        # 3. received audio topib update qilish
        received_audio = await get_audio_by_user_id_and_sentence_id(user_id, sentence_id, db)
        if received_audio:
          raise HTTPException(status_code=400, detail="Audio already exists")
        
        # 4. audio upload qilish
        file_ext = file.filename.split(".")[-1]
        filename = f"{uuid.uuid4()}.{file_ext}"
        file_path = os.path.join(UPLOAD_DIR, filename)

        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        except Exception as e:
            raise HTTPException(status_code=500, detail="Failed to save file")

        # 5. received audio qo'shish (oldin mavjudni update qilish)
        await update_received_audio_path_status(received_audio.id, file_path, db)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to save audio record")

    return {"status": "ok", "file_path": file_path, "id": received_audio.id}