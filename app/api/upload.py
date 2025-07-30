from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.models.received_audio import ReceivedAudio
from app.core.logging import get_logger
import shutil
import uuid
import os
from datetime import datetime, UTC

logger = get_logger("api.upload")
router = APIRouter(prefix="/upload", tags=["Upload"])

UPLOAD_DIR = "app/audio"

@router.post("/audio")
async def upload_audio(
    user_id: int = Form(...),
    sentence_id: int = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    logger.info(f"Audio upload request - user_id: {user_id}, sentence_id: {sentence_id}, filename: {file.filename}")

    file_ext = file.filename.split(".")[-1]
    filename = f"{uuid.uuid4()}.{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, filename)

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to save file")

    new_audio = ReceivedAudio(
        user_id=user_id,
        sentence_id=sentence_id,
        audio_path=file_path,
        created_at=datetime.now(UTC)
    )
    db.add(new_audio)
    
    try:
        await db.commit()
        await db.refresh(new_audio)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to save audio record")

    return {"status": "ok", "file_path": file_path, "id": new_audio.id}
