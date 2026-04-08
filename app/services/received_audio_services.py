from beanie import PydanticObjectId
from bson import ObjectId
from datetime import datetime, timedelta, timezone
UTC = timezone.utc
from fastapi import HTTPException

from app.models.sentence import Sentence
from app.models.received_audio import ReceivedAudio, AudioStatus
from app.models.checked_audio import CheckedAudio
from app.config import settings
from app.services.checked_audio_services import (
    get_or_create_checked_audio,
    update_checked_audio_reassign_to_thisUser,
    update_checked_audio_to_newUser,
)
from app.core.logging import get_logger

logger = get_logger("received_audio_services")


async def add_received_audio(user_id: PydanticObjectId, sentence_id: PydanticObjectId) -> ReceivedAudio:
    existing = await ReceivedAudio.find_one(
        ReceivedAudio.user == user_id,
        ReceivedAudio.sentence == sentence_id
    )
    if existing:
        raise HTTPException(status_code=400, detail="Audio already exists")
    received_audio = ReceivedAudio(user=user_id, sentence=sentence_id)
    await received_audio.insert()
    return received_audio


async def update_received_audio_to_newUser(user_id: PydanticObjectId, received_audio_id: PydanticObjectId) -> ReceivedAudio:
    received_audio = await ReceivedAudio.get(received_audio_id)
    if not received_audio:
        raise HTTPException(status_code=404, detail="Audio not found")
    received_audio.user = user_id
    received_audio.created_at = datetime.now(UTC)
    await received_audio.save()
    return received_audio


async def update_received_audio_reassign_to_thisUser(user_id: PydanticObjectId, sentence_id: PydanticObjectId) -> ReceivedAudio:
    received_audio = await ReceivedAudio.find_one(
        ReceivedAudio.user == user_id,
        ReceivedAudio.sentence == sentence_id
    )
    if not received_audio:
        raise HTTPException(status_code=404, detail="Audio not found")
    received_audio.created_at = datetime.now(UTC)
    await received_audio.save()
    return received_audio


async def get_audio_by_user_id_and_sentence_id(user_id: PydanticObjectId, sentence_id: PydanticObjectId) -> ReceivedAudio:
    received_audio = await ReceivedAudio.find_one(
        ReceivedAudio.user == user_id,
        ReceivedAudio.sentence == sentence_id
    )
    if not received_audio:
        raise HTTPException(status_code=404, detail="Audio not found")
    if received_audio.status == AudioStatus.approved:
        raise HTTPException(status_code=400, detail="This audio is already approved")
    return received_audio


async def update_received_audio_path_status(
    received_audio_id: PydanticObjectId,
    file_path: str,
    duration: float = None
) -> ReceivedAudio:
    received_audio = await ReceivedAudio.get(received_audio_id)
    if not received_audio:
        raise HTTPException(status_code=404, detail="Audio not found")
    received_audio.audio_path = file_path
    received_audio.status = AudioStatus.approved
    if duration is not None:
        received_audio.duration = duration
    await received_audio.save()
    return received_audio


async def get_audio_by_id(audio_id: PydanticObjectId) -> ReceivedAudio:
    received_audio = await ReceivedAudio.get(audio_id)
    if not received_audio:
        raise HTTPException(status_code=404, detail="Audio not found")
    return received_audio


async def get_received_audio_by_id(audio_id: PydanticObjectId) -> ReceivedAudio:
    return await get_audio_by_id(audio_id)


async def get_available_receivedAudio(user_id: PydanticObjectId, check_audio_count: int) -> ReceivedAudio:
    timeout_time = datetime.now(UTC) - timedelta(minutes=settings.pending_audio_timeout_minutes)

    # CHECK 1: User check limit
    if settings.user_check_audio_limit > 0 and check_audio_count >= settings.user_check_audio_limit:
        count_approved = await CheckedAudio.find(
            CheckedAudio.checked_by == user_id,
            CheckedAudio.status == AudioStatus.approved
        ).count()

        if count_approved >= settings.user_check_audio_limit:
            raise HTTPException(status_code=400, detail="Check audio limit reached")

        # Find own timed-out pending check
        checked_audio = await CheckedAudio.find_one(
            CheckedAudio.checked_by == user_id,
            CheckedAudio.status == AudioStatus.pending,
            CheckedAudio.checked_at < timeout_time
        )
        if checked_audio:
            await update_checked_audio_reassign_to_thisUser(checked_audio.id)
            return await get_audio_by_id(checked_audio.audio.ref.id)
        raise HTTPException(status_code=400, detail="Check audio limit reached, please wait")

    # CHECK 2: Find available audio via aggregation
    try:
        pipeline = [
            {
                "$match": {
                    "audio_path": {"$ne": None},
                    "status": "approved"
                }
            },
            {
                "$lookup": {
                    "from": "checked_audio",
                    "localField": "_id",
                    "foreignField": "audio.$id",
                    "as": "checks"
                }
            },
            {
                "$match": {
                    "checks.checked_by.$id": {"$ne": ObjectId(str(user_id))}
                }
            },
            {
                "$addFields": {
                    "active_checks": {
                        "$filter": {
                            "input": "$checks",
                            "as": "c",
                            "cond": {
                                "$or": [
                                    {"$eq": ["$$c.status", "approved"]},
                                    {
                                        "$and": [
                                            {"$eq": ["$$c.status", "pending"]},
                                            {"$gt": ["$$c.checked_at", timeout_time]}
                                        ]
                                    }
                                ]
                            }
                        }
                    }
                }
            },
            {
                "$match": {
                    "$expr": {"$lt": [{"$size": "$active_checks"}, settings.audio_check_limit]}
                }
            },
            {"$sample": {"size": 1}}
        ]

        results = await ReceivedAudio.aggregate(pipeline).to_list()
        if results:
            audio_id = results[0]["_id"]
            received_audio = await ReceivedAudio.get(audio_id, fetch_links=True)
            if received_audio:
                await get_or_create_checked_audio(user_id, received_audio.id)
                return received_audio
    except Exception as e:
        logger.error(f"Aggregation error in get_available_receivedAudio: {e}")

    # CHECK 3: Find timed-out pending check from other users
    try:
        pipeline_pending = [
            {
                "$match": {
                    "audio_path": {"$ne": None},
                    "status": "approved"
                }
            },
            {
                "$lookup": {
                    "from": "checked_audio",
                    "localField": "_id",
                    "foreignField": "audio.$id",
                    "as": "checks"
                }
            },
            {"$unwind": "$checks"},
            {
                "$match": {
                    "checks.checked_by.$id": {"$ne": ObjectId(str(user_id))},
                    "checks.status": "pending",
                    "checks.checked_at": {"$lt": timeout_time}
                }
            },
            {"$sample": {"size": 1}}
        ]
        results_pending = await ReceivedAudio.aggregate(pipeline_pending).to_list()
        if results_pending:
            audio_id = results_pending[0]["_id"]
            received_audio = await ReceivedAudio.get(audio_id, fetch_links=True)
            checked_audio_id = results_pending[0]["checks"]["_id"]
            if received_audio:
                await update_checked_audio_to_newUser(user_id, checked_audio_id)
                return received_audio
    except Exception as e:
        logger.error(f"Pending aggregation error: {e}")

    # CHECK 4: Own timed-out pending check
    try:
        pipeline_own = [
            {
                "$match": {
                    "audio_path": {"$ne": None},
                    "status": "approved"
                }
            },
            {
                "$lookup": {
                    "from": "checked_audio",
                    "localField": "_id",
                    "foreignField": "audio.$id",
                    "as": "checks"
                }
            },
            {"$unwind": "$checks"},
            {
                "$match": {
                    "checks.checked_by.$id": ObjectId(str(user_id)),
                    "checks.status": "pending",
                    "checks.checked_at": {"$lt": timeout_time}
                }
            },
            {"$sample": {"size": 1}}
        ]
        results_own = await ReceivedAudio.aggregate(pipeline_own).to_list()
        if results_own:
            audio_id = results_own[0]["_id"]
            received_audio = await ReceivedAudio.get(audio_id, fetch_links=True)
            checked_audio_id = results_own[0]["checks"]["_id"]
            if received_audio:
                await update_checked_audio_reassign_to_thisUser(checked_audio_id)
                return received_audio
    except Exception as e:
        logger.error(f"Own pending aggregation error: {e}")

    raise HTTPException(status_code=404, detail="No available audio found")
