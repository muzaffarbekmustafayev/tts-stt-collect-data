from beanie import PydanticObjectId
from fastapi import APIRouter, Depends
from app.schemas.checked_audio import SecondCheckUpdate, CheckedAudioOut
from app.core.logging import get_logger
from app.services.checked_audio_services import get_audio_for_second_check_service, update_second_checked_audio_result
from app.services.admin_user_service import get_current_checker_user

logger = get_logger("api.checked_audio")
router = APIRouter(prefix="/second-check", tags=["Second Check"])

@router.post("/get-audio", response_model=CheckedAudioOut, dependencies=[Depends(get_current_checker_user)])
async def get_audio_for_second_check(current_user: dict = Depends(get_current_checker_user)):
    user_id = current_user["id"]
    audio = await get_audio_for_second_check_service(user_id)
    
    # Map to schema-compatible dict with string IDs
    out_data = audio.model_dump(mode="json")
    out_data["id"] = str(audio.id)
    out_data["audio_id"] = str(audio.audio.id) if audio.audio else None
    out_data["checked_by"] = str(audio.checked_by.id) if audio.checked_by else None
    return out_data
    

@router.put("/update/{id}", response_model=CheckedAudioOut, dependencies=[Depends(get_current_checker_user)])
async def update_second_checked_audio_by_id(id: PydanticObjectId, req_checked_audio: SecondCheckUpdate, current_user: dict = Depends(get_current_checker_user)):
    user_id = current_user["id"]
    checked_audio = await update_second_checked_audio_result(id, req_checked_audio.second_check_result, user_id)
    
    # Map to schema-compatible dict with string IDs
    out_data = checked_audio.model_dump(mode="json")
    out_data["id"] = str(checked_audio.id)
    out_data["audio_id"] = str(checked_audio.audio.id) if checked_audio.audio else None
    out_data["checked_by"] = str(checked_audio.checked_by.id) if checked_audio.checked_by else None
    return out_data