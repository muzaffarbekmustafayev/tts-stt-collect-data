from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, HTTPException
from app.models.checked_audio import CheckedAudio
from app.schemas.checked_audio import CheckedAudioCreate
from app.core.logging import get_logger
from app.services.user_service import get_user_by_userId
from app.services.received_audio_services import get_audio_by_id
from app.services.checked_audio_services import (
    checked_audio_and_update,
    get_checked_audio_by_id,
    update_checked_audio_result_status,
)
from app.services.admin_user_service import get_current_admin_user
from app.models.received_audio import AudioStatus

logger = get_logger("api.checked_audio")
router = APIRouter(prefix="/checked-audio", tags=["Checked Audio"])


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


@router.post("/")
async def check_audio(data: CheckedAudioCreate):
    await get_user_by_userId(data.checked_by)
    await get_audio_by_id(data.audio_id)
    result = await checked_audio_and_update(data.checked_by, data.audio_id, data.is_correct)
    return _serialize(result)


@router.get("/by-audio/{audio_id}")
async def get_check_by_audio(audio_id: PydanticObjectId):
    check_list = await CheckedAudio.find(
        CheckedAudio.audio == audio_id,
        fetch_links=True
    ).to_list()

    result = []
    for c in check_list:
        d = _serialize(c)
        d["checked_by_name"] = c.checked_by.name if c.checked_by else None
        result.append(d)
    return result


@router.put("/{id}", dependencies=[Depends(get_current_admin_user)])
async def update_checked_audio_by_id(id: PydanticObjectId, req: CheckedAudioCreate):
    ca = await get_checked_audio_by_id(id)
    ca.checked_by = req.checked_by
    ca.is_correct = req.is_correct
    ca.comment = req.comment
    if req.status:
        ca.status = req.status
    await ca.save()
    return _serialize(ca)


@router.delete("/{id}", dependencies=[Depends(get_current_admin_user)])
async def delete_checked_audio_by_id(id: PydanticObjectId):
    ca = await get_checked_audio_by_id(id)
    await ca.delete()
    return {"message": "Deleted", "id": str(id)}
