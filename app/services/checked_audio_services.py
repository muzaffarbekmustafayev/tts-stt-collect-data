from beanie import PydanticObjectId
from datetime import datetime, timedelta, UTC
from fastapi import HTTPException
from typing import Optional

from app.models.sentence import Sentence
from app.models.received_audio import ReceivedAudio, AudioStatus
from app.models.checked_audio import CheckedAudio
from app.config import settings

async def add_checked_audio(user_id: PydanticObjectId, audio_id: PydanticObjectId) -> CheckedAudio | None:
    existing = await CheckedAudio.find_one(
        CheckedAudio.checked_by.id == user_id,
        CheckedAudio.audio.id == audio_id
    )
    if existing:
        raise HTTPException(status_code=400, detail="Checked audio already exists")
    
    checked_audio = CheckedAudio(checked_by=user_id, audio=audio_id, status=AudioStatus.pending)
    await checked_audio.insert()
    return checked_audio

async def update_checked_audio_to_newUser(user_id: PydanticObjectId, checked_audio_id: PydanticObjectId) -> CheckedAudio | None:
    checked_audio = await CheckedAudio.get(checked_audio_id)
    if checked_audio:
        checked_audio.checked_by = user_id
        checked_audio.checked_at = datetime.now(UTC)
        await checked_audio.save()
        return checked_audio
    raise HTTPException(status_code=404, detail="Audio not found")
  
async def update_checked_audio_reassign_to_thisUser(checked_audio_id: PydanticObjectId) -> CheckedAudio | None:
    checked_audio = await CheckedAudio.get(checked_audio_id)
    if checked_audio:
        checked_audio.checked_at = datetime.now(UTC)
        await checked_audio.save()
        return checked_audio
    raise HTTPException(status_code=404, detail="Audio not found")
    
async def get_audio_by_user_id_and_sentence_id(user_id: PydanticObjectId, sentence_id: PydanticObjectId) -> ReceivedAudio | None:
    received_audio = await ReceivedAudio.find_one(
        ReceivedAudio.user.id == user_id,
        ReceivedAudio.sentence.id == sentence_id,
        ReceivedAudio.status == AudioStatus.pending
    )
    if not received_audio:
      raise HTTPException(status_code=404, detail="Audio not found")
    return received_audio

async def update_checked_audio_result_status(checked_audio_id: PydanticObjectId, status: AudioStatus, is_correct: bool) -> CheckedAudio | None:
    checked_audio = await CheckedAudio.get(checked_audio_id)
    if not checked_audio:
      raise HTTPException(status_code=404, detail="Checked audio not found")
    checked_audio.status = status
    checked_audio.is_correct = is_correct
    await checked_audio.save()
    return checked_audio
  
async def checked_audio_and_update(user_id: PydanticObjectId, audio_id: PydanticObjectId, is_correct: bool) -> CheckedAudio | None:
    checked_audio = await CheckedAudio.find_one(
        CheckedAudio.checked_by.id == user_id,
        CheckedAudio.audio.id == audio_id,
        CheckedAudio.status == AudioStatus.pending
    )
    if not checked_audio:
      raise HTTPException(status_code=404, detail="Checked audio not found")
    checked_audio.status = AudioStatus.approved
    checked_audio.is_correct = is_correct
    await checked_audio.save()
    return checked_audio

async def get_checked_audio_by_id(checked_audio_id: PydanticObjectId) -> CheckedAudio | None:
    checked_audio = await CheckedAudio.get(checked_audio_id)
    if not checked_audio:
      raise HTTPException(status_code=404, detail="Checked audio not found")
    return checked_audio

#========================== second check services ========================

async def get_audio_for_second_check_service(user_id: PydanticObjectId) -> CheckedAudio | None:
    checked_audio = await CheckedAudio.find_one(
        CheckedAudio.status == AudioStatus.approved,
        CheckedAudio.second_checker == None
    ).sort(-CheckedAudio.checked_at)

    if checked_audio:
        checked_audio.second_checker = user_id
        await checked_audio.save()
        return checked_audio

    raise HTTPException(status_code=404, detail="Audio not found")

async def update_second_checked_audio_result(checked_audio_id: PydanticObjectId, second_check_result: bool, user_id: PydanticObjectId) -> CheckedAudio | None:
    checked_audio = await CheckedAudio.find_one(
        CheckedAudio.id == checked_audio_id,
        CheckedAudio.second_checker.id == user_id
    )
    if checked_audio:
      checked_audio.second_check_result = second_check_result
      checked_audio.second_checked_at = datetime.now(UTC)
      await checked_audio.save()
      return checked_audio
    raise HTTPException(status_code=404, detail="Checked audio not found")