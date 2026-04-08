from beanie import PydanticObjectId
from fastapi import APIRouter, Depends
from app.schemas.checked_audio import SecondCheckUpdate
from app.core.logging import get_logger
from app.services.checked_audio_services import get_audio_for_second_check_service, update_second_checked_audio_result
from app.services.admin_user_service import get_current_checker_user
from app.models.checked_audio import CheckedAudio

logger = get_logger("api.second_check")
router = APIRouter(prefix="/second-check", tags=["Second Check"])


def _serialize(ca: CheckedAudio) -> dict:
    return {
        "id": str(ca.id),
        "audio_id": str(ca.audio.ref.id) if ca.audio else None,
        "checked_by": str(ca.checked_by.ref.id) if ca.checked_by else None,
        "is_correct": ca.is_correct,
        "comment": ca.comment,
        "status": ca.status,
        "checked_at": ca.checked_at.isoformat() if ca.checked_at else None,
        "second_checker_id": str(ca.second_checker.ref.id) if ca.second_checker else None,
        "second_check_result": ca.second_check_result,
        "second_checked_at": ca.second_checked_at.isoformat() if ca.second_checked_at else None,
    }


@router.post("/get-audio", dependencies=[Depends(get_current_checker_user)])
async def get_audio_for_second_check(current_user: dict = Depends(get_current_checker_user)):
    audio = await get_audio_for_second_check_service(current_user["id"])
    return _serialize(audio)


@router.put("/update/{id}", dependencies=[Depends(get_current_checker_user)])
async def update_second_checked_audio_by_id(
    id: PydanticObjectId,
    req: SecondCheckUpdate,
    current_user: dict = Depends(get_current_checker_user)
):
    ca = await update_second_checked_audio_result(id, req.second_check_result, current_user["id"])
    return _serialize(ca)
