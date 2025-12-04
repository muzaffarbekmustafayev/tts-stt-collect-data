from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.checked_audio import SecondCheckUpdate, CheckedAudioOut
from app.core.logging import get_logger
from app.services.checked_audio_services import get_audio_for_second_check_service, update_second_checked_audio_result
from app.services.admin_user_service import get_current_checker_user

logger = get_logger("api.checked_audio")
router = APIRouter(prefix="/second-check", tags=["Second Check"])

@router.post("/get-audio", response_model=CheckedAudioOut, dependencies=[Depends(get_current_checker_user)])
async def get_audio_for_second_check(db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_checker_user)):
    user_id = current_user["id"]
    audio = await get_audio_for_second_check_service(user_id, db)
    return audio
    

@router.put("/update/{id}", response_model=CheckedAudioOut, dependencies=[Depends(get_current_checker_user)])
async def update_second_checked_audio_by_id(id: int, req_checked_audio: SecondCheckUpdate, db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_checker_user)):
    user_id = current_user["id"]
    checked_audio = await update_second_checked_audio_result(id, req_checked_audio.second_check_result, user_id, db)
    return checked_audio