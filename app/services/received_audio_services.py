from beanie import PydanticObjectId
from datetime import datetime, timedelta, UTC
from fastapi import HTTPException
from typing import Optional

from app.models.sentence import Sentence
from app.models.received_audio import ReceivedAudio, AudioStatus
from app.models.checked_audio import CheckedAudio
from app.config import settings
from app.services.checked_audio_services import update_checked_audio_reassign_to_thisUser, add_checked_audio, update_checked_audio_to_newUser

async def add_received_audio(user_id: PydanticObjectId, sentence_id: PydanticObjectId) -> ReceivedAudio | None:
    existing = await ReceivedAudio.find_one(
        ReceivedAudio.user.id == user_id,
        ReceivedAudio.sentence.id == sentence_id
    )
    if existing:
        raise HTTPException(status_code=400, detail="Audio already exists")
    
    received_audio = ReceivedAudio(user=user_id, sentence=sentence_id)
    await received_audio.insert()
    return received_audio

async def get_or_create_received_audio(user_id: PydanticObjectId, sentence_id: PydanticObjectId) -> ReceivedAudio:
    received_audio = await ReceivedAudio.find_one(
        ReceivedAudio.user.id == user_id,
        ReceivedAudio.sentence.id == sentence_id
    )
    if received_audio:
        return received_audio
    
    received_audio = ReceivedAudio(user=user_id, sentence=sentence_id)
    await received_audio.insert()
    return received_audio

async def update_received_audio_to_newUser(user_id: PydanticObjectId, received_audio_id: PydanticObjectId) -> ReceivedAudio | None:
    received_audio = await ReceivedAudio.get(received_audio_id)
    if received_audio:
        received_audio.user = user_id
        received_audio.created_at = datetime.now(UTC)
        await received_audio.save()
        return received_audio
    raise HTTPException(status_code=404, detail="Audio not found")
  
async def update_received_audio_reassign_to_thisUser(user_id: PydanticObjectId, sentence_id: PydanticObjectId) -> ReceivedAudio | None:
    received_audio = await ReceivedAudio.find_one(
        ReceivedAudio.user.id == user_id,
        ReceivedAudio.sentence.id == sentence_id
    )
    if received_audio:
        received_audio.created_at = datetime.now(UTC)
        await received_audio.save()
        return received_audio
    raise HTTPException(status_code=404, detail="Audio not found")
    
async def get_audio_by_user_id_and_sentence_id(user_id: PydanticObjectId, sentence_id: PydanticObjectId) -> ReceivedAudio | None:
    received_audio = await ReceivedAudio.find_one(
        ReceivedAudio.user.id == user_id,
        ReceivedAudio.sentence.id == sentence_id
    )
    if not received_audio:
      raise HTTPException(status_code=404, detail="Audio not found")
    if received_audio.status == AudioStatus.approved:
      raise HTTPException(status_code=400, detail="This audio is already approved")
    return received_audio

async def update_received_audio_path_status(received_audio_id: PydanticObjectId, file_path: str, duration: float = None) -> ReceivedAudio | None:
    received_audio = await ReceivedAudio.get(received_audio_id)
    if not received_audio:
      raise HTTPException(status_code=404, detail="Audio not found")
    received_audio.audio_path = file_path
    received_audio.status = AudioStatus.approved
    if duration is not None:
        received_audio.duration = duration
    await received_audio.save()
    return received_audio


async def get_available_receivedAudio(user_id: PydanticObjectId, check_audio_count: int) -> ReceivedAudio | None:
    timeout_time = datetime.now(UTC) - timedelta(minutes=settings.pending_audio_timeout_minutes)
    
    if settings.user_check_audio_limit > 0:
      if check_audio_count >= settings.user_check_audio_limit:
        count_approved = await CheckedAudio.find(
            CheckedAudio.checked_by.id == user_id,
            CheckedAudio.status == AudioStatus.approved
        ).count()
        
        if count_approved >= settings.user_check_audio_limit:
          raise HTTPException(status_code=400, detail="The user's sending result limit is over, please wait for the next sentence")
        
        checked_audio = await CheckedAudio.find_one(
            CheckedAudio.checked_by.id == user_id,
            CheckedAudio.status == AudioStatus.pending,
            CheckedAudio.checked_at < timeout_time
        )
        if checked_audio:
          await update_checked_audio_reassign_to_thisUser(checked_audio.id)
          return await get_audio_by_id(checked_audio.audio.id)
        else:  
          raise HTTPException(status_code=400, detail="The user's sending audio limit is over, please wait for the next sentence")
      
    # CHECK 2: Find random audio that hasn't reached check limit and wasn't sent/checked by this user
    # This is slightly more complex in NoSQL but we can use MongoDB's random if needed or just find first.
    # We'll use aggregation for random selection if possible or just find one.
    
    # Actually, Beanie doesn't have a built-in random, so we might need a custom aggregation or just find all and pick one.
    # For now, let's use a simple approach.
    
    # Audio not checked by this user
    # Motor/Beanie aggregation for random
    pipeline = [
        {"$match": {
            "user.$id": {"$ne": user_id},
            "audio_path": {"$ne": None}
        }},
        {"$lookup": {
            "from": "checked_audio",
            "localField": "_id",
            "foreignField": "audio.$id",
            "as": "checks"
        }},
        {"$match": {
            "checks.checked_by.$id": {"$ne": user_id}
        }},
        # Filter where active checks count < limit
        # This is tricky with NoSQL. We'll simplify:
        {"$addFields": {
            "active_checks": {
                "$filter": {
                    "input": "$checks",
                    "as": "c",
                    "cond": {
                        "$or": [
                            {"$eq": ["$$c.status", AudioStatus.approved]},
                            {"$and": [
                                {"$eq": ["$$c.status", AudioStatus.pending]},
                                {"$gt": ["$$c.checked_at", timeout_time]}
                            ]}
                        ]
                    }
                }
            }
        }},
        {"$match": {
            "$expr": {"$lt": [{"$size": "$active_checks"}, settings.audio_check_limit]}
        }},
        {"$sample": {"size": 1}}
    ]
    
    results = await ReceivedAudio.aggregate(pipeline).to_list()
    if results:
        audio_id = results[0]["_id"]
        received_audio = await ReceivedAudio.get(audio_id, fetch_links=True)
        await add_checked_audio(user_id, received_audio.id)
        return received_audio

    # CHECK 3: Pending and timeout
    pipeline_pending = [
        {"$match": {
            "user.$id": {"$ne": user_id},
            "audio_path": {"$ne": None}
        }},
        {"$lookup": {
            "from": "checked_audio",
            "localField": "_id",
            "foreignField": "audio.$id",
            "as": "checks"
        }},
        {"$unwind": "$checks"},
        {"$match": {
            "checks.checked_by.$id": {"$ne": user_id},
            "checks.status": AudioStatus.pending,
            "checks.checked_at": {"$lt": timeout_time}
        }},
        {"$sample": {"size": 1}}
    ]
    results_pending = await ReceivedAudio.aggregate(pipeline_pending).to_list()
    if results_pending:
        audio_id = results_pending[0]["_id"]
        received_audio = await ReceivedAudio.get(audio_id, fetch_links=True)
        checked_audio_id = results_pending[0]["checks"]["_id"]
        await update_checked_audio_to_newUser(user_id, checked_audio_id)
        return received_audio

    # CHECK 4: User's own pending timeout
    pipeline_own = [
        {"$match": {
            "user.$id": {"$ne": user_id},
            "audio_path": {"$ne": None}
        }},
        {"$lookup": {
            "from": "checked_audio",
            "localField": "_id",
            "foreignField": "audio.$id",
            "as": "checks"
        }},
        {"$unwind": "$checks"},
        {"$match": {
            "checks.checked_by.$id": user_id,
            "checks.status": AudioStatus.pending,
            "checks.checked_at": {"$lt": timeout_time}
        }},
        {"$sample": {"size": 1}}
    ]
    results_own = await ReceivedAudio.aggregate(pipeline_own).to_list()
    if results_own:
        audio_id = results_own[0]["_id"]
        received_audio = await ReceivedAudio.get(audio_id, fetch_links=True)
        checked_audio_id = results_own[0]["checks"]["_id"]
        await update_checked_audio_reassign_to_thisUser(checked_audio_id)
        return received_audio

    raise HTTPException(status_code=404, detail="No available audio found")

async def get_audio_by_id(audio_id: PydanticObjectId) -> ReceivedAudio | None:
    received_audio = await ReceivedAudio.get(audio_id)
    if not received_audio:
        raise HTTPException(status_code=404, detail="Audio not found")
    return received_audio

async def get_received_audio_by_id(audio_id: PydanticObjectId) -> ReceivedAudio | None:
    return await get_audio_by_id(audio_id)
