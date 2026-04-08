from beanie import PydanticObjectId
from fastapi import APIRouter, UploadFile, Depends, HTTPException
from app.models.received_audio import ReceivedAudio
from app.models.checked_audio import CheckedAudio
from app.core.logging import get_logger
from app.services.user_service import get_user_by_userId, check_user_check_audio_limit
from app.services.sentence_service import get_sentence_by_id
from app.services.received_audio_services import (
    get_audio_by_user_id_and_sentence_id,
    update_received_audio_path_status,
    get_available_receivedAudio,
    get_received_audio_by_id,
)
from app.services.admin_user_service import get_current_admin_user
import shutil, uuid, os
from pathlib import Path
from app.config import MEDIA_DIR

logger = get_logger("api.received_audio")
router = APIRouter(prefix="/received-audio", tags=["Received Audio"])

UPLOAD_DIR = os.path.join(MEDIA_DIR, "audio")


def ensure_directories_exist():
    os.makedirs(MEDIA_DIR, exist_ok=True)
    os.makedirs(UPLOAD_DIR, exist_ok=True)


def _serialize(a: ReceivedAudio) -> dict:
    return {
        "id": str(a.id),
        "user_id": str(a.user.ref.id) if a.user else None,
        "sentence_id": str(a.sentence.ref.id) if a.sentence else None,
        "audio_path": a.audio_path,
        "duration": a.duration,
        "status": a.status,
        "created_at": a.created_at.isoformat() if a.created_at else None,
    }


def _serialize_with_links(a: ReceivedAudio) -> dict:
    return {
        "id": str(a.id),
        "user_id": str(a.user.id) if a.user else None,
        "user_name": a.user.name if a.user else None,
        "sentence_id": str(a.sentence.id) if a.sentence else None,
        "sentence": a.sentence.text if a.sentence else None,
        "audio_path": a.audio_path,
        "duration": a.duration,
        "status": a.status,
        "created_at": a.created_at.isoformat() if a.created_at else None,
    }


@router.post("/")
async def create_received_audio(
    user_id: PydanticObjectId,
    sentence_id: PydanticObjectId,
    file: UploadFile
):
    ensure_directories_exist()

    await get_user_by_userId(user_id)
    await get_sentence_by_id(sentence_id)

    received_audio = await get_audio_by_user_id_and_sentence_id(user_id, sentence_id)

    ext = Path(file.filename or "audio.ogg").suffix.lower() or ".ogg"
    file_name = f"{uuid.uuid4()}{ext}"
    file_path = os.path.join(UPLOAD_DIR, file_name)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    await file.close()

    relative_path = f"audio/{file_name}"
    updated = await update_received_audio_path_status(received_audio.id, relative_path)
    return _serialize(updated)


@router.get("/{user_id}")
async def get_audio_by_user(user_id: PydanticObjectId):
    user = await get_user_by_userId(user_id)
    check_count = await check_user_check_audio_limit(user.id)
    received_audio = await get_available_receivedAudio(user_id, check_count)
    await received_audio.fetch_all_links()
    return _serialize_with_links(received_audio)


@router.get("/by-id/{id}")
async def get_audio_by_id_endpoint(id: PydanticObjectId):
    audio = await get_received_audio_by_id(id)
    await audio.fetch_all_links()
    return _serialize_with_links(audio)


@router.put("/{id}", dependencies=[Depends(get_current_admin_user)])
async def update_received_audio_by_id(id: PydanticObjectId):
    audio = await get_received_audio_by_id(id)
    await audio.save()
    return _serialize(audio)


@router.delete("/{id}", dependencies=[Depends(get_current_admin_user)])
async def delete_received_audio_by_id(id: PydanticObjectId):
    audio = await get_received_audio_by_id(id)

    checked = await CheckedAudio.find_one(CheckedAudio.audio == id)
    if checked:
        raise HTTPException(status_code=400, detail="Cannot delete audio that has been checked")

    if audio.audio_path:
        full_path = os.path.join(MEDIA_DIR, audio.audio_path)
        if os.path.exists(full_path):
            os.remove(full_path)

    await audio.delete()
    return {"message": "Deleted", "id": str(id)}
