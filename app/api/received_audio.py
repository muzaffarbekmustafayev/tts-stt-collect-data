from beanie import PydanticObjectId
from app.schemas.received_audio import ReceivedAudioCreate, ReceivedAudioOut, ReceivedAudioOutPost
from fastapi import APIRouter, UploadFile, Depends, HTTPException
from app.models.received_audio import ReceivedAudio
from app.models.checked_audio import CheckedAudio
from app.core.logging import get_logger
from app.services.user_service import get_user_by_userId, check_user_check_audio_limit
from app.services.sentence_service import get_sentence_by_id
from app.services.received_audio_services import get_audio_by_user_id_and_sentence_id, update_received_audio_path_status, get_available_receivedAudio, add_received_audio, get_received_audio_by_id
import shutil
import uuid
from pathlib import Path
import os
from datetime import datetime, UTC
from app.config import MEDIA_DIR
from app.services.admin_user_service import get_current_admin_user

logger = get_logger("api.received_audio")
router = APIRouter(prefix="/received-audio", tags=["Received Audio"])

UPLOAD_DIR = os.path.join(MEDIA_DIR, "audio")

# Papka yaratish funksiyasi
def ensure_directories_exist():
    """Kerakli papkalarni yaratadi agar mavjud bo'lmasa"""
    os.makedirs(MEDIA_DIR, exist_ok=True)
    os.makedirs(UPLOAD_DIR, exist_ok=True)

#upload audio va received audio topib update qilish
@router.post("/", response_model=ReceivedAudioOutPost)
async def create_received_audio(
    user_id: PydanticObjectId,
    sentence_id: PydanticObjectId,
    file: UploadFile
):
    logger.info(f"Audio upload request - user_id: {user_id}, sentence_id: {sentence_id}, filename: {file.filename}")
    
    if not user_id or not sentence_id:
        raise HTTPException(status_code=400, detail="Invalid request")

    # Papkalarni yaratish
    ensure_directories_exist()
    
    ext = Path(file.filename or "").suffix.lower()

    # 3. user va sentence aniqlash
    await get_user_by_userId(user_id)
    await get_sentence_by_id(sentence_id)
   
    # 4. Mavjud audio borligini tekshirish
    received_audio = await get_audio_by_user_id_and_sentence_id(user_id, sentence_id)
    
    # 5. Faylni saqlash
    file_name = f"{uuid.uuid4()}{ext}"
    file_path = os.path.join(UPLOAD_DIR, file_name)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    await file.close()

    # 6. received audio update qilish
    relative_path = f"audio/{file_name}"
    updated_audio = await update_received_audio_path_status(received_audio_id=received_audio.id, file_path=relative_path)
    
    return updated_audio


# user id bo'yicha check qilish uchun audio olish
@router.get("/{user_id}", response_model=ReceivedAudioOut)
async def get_audio_by_user(user_id: PydanticObjectId):
    # 1. user check
    user = await get_user_by_userId(user_id)
    # 2. user limit
    check_audio_count = await check_user_check_audio_limit(user.id)
    # 3. get audio
    received_audio = await get_available_receivedAudio(user_id, check_audio_count)
    if not received_audio:
        raise HTTPException(status_code=404, detail="Audio not found")
    
    # Fetch sentence text
    sentence = await get_sentence_by_id(received_audio.sentence.id)
    
    # Convert to schema compatible dict or object
    # ReceivedAudioOut expects 'sentence' as string
    out_data = received_audio.model_dump()
    out_data["id"] = received_audio.id
    out_data["user_id"] = received_audio.user.id
    out_data["sentence_id"] = received_audio.sentence.id
    out_data["sentence"] = sentence.text
    return out_data

# update received audio by id
@router.put("/{id}", response_model=ReceivedAudioOut, dependencies=[Depends(get_current_admin_user)])
async def update_received_audio_by_id(id: PydanticObjectId, received_audio_data: ReceivedAudioCreate):
    received_audio = await get_received_audio_by_id(id)
    # Beanie specific update logic if needed, or just service call
    # Here we just refresh/save for now as the original code was minimal
    await received_audio.save()
    
    sentence = await get_sentence_by_id(received_audio.sentence.id)
    out_data = received_audio.model_dump()
    out_data["id"] = received_audio.id
    out_data["user_id"] = received_audio.user.id
    out_data["sentence_id"] = received_audio.sentence.id
    out_data["sentence"] = sentence.text
    return out_data

# delete received audio
@router.delete("/{id}", response_model=ReceivedAudioOutPost, dependencies=[Depends(get_current_admin_user)])
async def delete_received_audio_by_id(id: PydanticObjectId):
    received_audio = await get_received_audio_by_id(id)
    
    checked_audio = await CheckedAudio.find_one(CheckedAudio.audio.id == id)
    if checked_audio:
        raise HTTPException(status_code=400, detail="You can't delete this audio because it has in checked_audio table")
    
    if received_audio.audio_path:
        full_path = os.path.join(MEDIA_DIR, received_audio.audio_path)
        if os.path.exists(full_path):
            os.remove(full_path)
    
    await received_audio.delete()
    return received_audio


@router.get("/by-id/{id}", response_model=ReceivedAudioOut)
async def get_audio_by_id_endpoint(id: PydanticObjectId):
    received_audio = await get_received_audio_by_id(id)
    sentence = await get_sentence_by_id(received_audio.sentence.id)
    
    out_data = received_audio.model_dump()
    out_data["id"] = received_audio.id
    out_data["user_id"] = received_audio.user.id
    out_data["sentence_id"] = received_audio.sentence.id
    out_data["sentence"] = sentence.text
    return out_data