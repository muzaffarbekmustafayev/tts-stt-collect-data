from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, HTTPException
from app.models.checked_audio import CheckedAudio
from app.schemas.checked_audio import CheckedAudioCreate, CheckedAudioOut
from app.core.logging import get_logger
from app.services.user_service import get_user_by_userId
from app.services.received_audio_services import get_audio_by_id
from app.services.checked_audio_services import checked_audio_and_update, get_checked_audio_by_id
from app.services.admin_user_service import get_current_admin_user

logger = get_logger("api.checked_audio")
router = APIRouter(prefix="/checked-audio", tags=["Checked Audio"])

@router.post("/", response_model=CheckedAudioOut)
async def check_audio(data: CheckedAudioCreate):
    # checked_by, audio_id, is_correct
    # 1. check user
    await get_user_by_userId(data.checked_by)
    # 2. check audio_id
    await get_audio_by_id(data.audio_id)
    # 3. check if audio is already checked
    result = await checked_audio_and_update(data.checked_by, data.audio_id, data.is_correct)
    
    # Map to schema-compatible dict with string IDs for reliable JSON serialization
    out_data = result.model_dump(mode="json")
    out_data["id"] = str(result.id)
    out_data["audio_id"] = str(result.audio.id) if result.audio else None
    out_data["checked_by"] = str(result.checked_by.id) if result.checked_by else None
    return out_data
    

@router.get("/by-audio/{audio_id}", response_model=list[CheckedAudioOut])
async def get_check_by_audio(audio_id: PydanticObjectId):
    check_list = await CheckedAudio.find(CheckedAudio.audio.id == audio_id, fetch_links=True).to_list()
    logger.info(f"Found {len(check_list)} checked audio records for audio {audio_id}")
    
    formatted = []
    for c in check_list:
        d = c.model_dump(mode="json")
        d["id"] = str(c.id)
        d["audio_id"] = str(c.audio.id) if c.audio else None
        d["checked_by"] = str(c.checked_by.id) if c.checked_by else None
        d["checked_by_name"] = c.checked_by.name if c.checked_by else None
        formatted.append(d)
    return formatted


@router.put("/{id}", response_model=CheckedAudioOut, dependencies=[Depends(get_current_admin_user)])
async def update_checked_audio_by_id(id: PydanticObjectId, req_checked_audio: CheckedAudioCreate):
    checked_audio = await get_checked_audio_by_id(id)
    checked_audio.checked_by = req_checked_audio.checked_by
    checked_audio.is_correct = req_checked_audio.is_correct
    checked_audio.comment = req_checked_audio.comment
    checked_audio.status = req_checked_audio.status
    await checked_audio.save()
    
    out_data = checked_audio.model_dump(mode="json")
    out_data["id"] = str(checked_audio.id)
    out_data["audio_id"] = str(checked_audio.audio.id) if checked_audio.audio else None
    out_data["checked_by"] = str(checked_audio.checked_by.id) if checked_audio.checked_by else None
    return out_data


@router.delete("/{id}", response_model=CheckedAudioOut, dependencies=[Depends(get_current_admin_user)])
async def delete_checked_audio_by_id(id: PydanticObjectId):
    checked_audio = await get_checked_audio_by_id(id)
    if not checked_audio:
        raise HTTPException(status_code=404, detail="Checked audio not found")
    
    out_data = checked_audio.model_dump()
    out_data["id"] = checked_audio.id
    out_data["audio_id"] = checked_audio.audio.id
    out_data["checked_by"] = checked_audio.checked_by.id
    
    await checked_audio.delete()
    return out_data