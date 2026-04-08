from beanie import PydanticObjectId
from datetime import datetime, timedelta, timezone
UTC = timezone.utc
from fastapi import HTTPException
from typing import Optional

from app.models.sentence import Sentence
from app.models.received_audio import ReceivedAudio, AudioStatus
from app.config import settings
from app.services.received_audio_services import add_received_audio, update_received_audio_to_newUser, update_received_audio_reassign_to_thisUser
from app.core.logging import get_logger

logger = get_logger("sentence_service")

async def get_available_sentence(user_id: PydanticObjectId, sent_audio_count: int) -> Sentence | None:
    """
    Optimized sentence selection with multiple fallback strategies
    """
    timeout_time = datetime.now(UTC) - timedelta(minutes=settings.pending_audio_timeout_minutes)

    # CHECK 1: User sent audio limit
    if sent_audio_count >= settings.user_sent_audio_limit:
        count_approved = await ReceivedAudio.find(
            ReceivedAudio.user.id == user_id,
            ReceivedAudio.status == AudioStatus.approved
        ).count()
        
        if count_approved >= settings.user_sent_audio_limit:
            raise HTTPException(
                status_code=400, 
                detail="The user's sending audio limit is over, please wait for the next sentence"
            )
        
        # Check for own pending timeout
        pending_audio = await ReceivedAudio.find_one(
            ReceivedAudio.user.id == user_id,
            ReceivedAudio.status == AudioStatus.pending,
            ReceivedAudio.created_at < timeout_time
        )
        if pending_audio:
            await update_received_audio_reassign_to_thisUser(user_id, pending_audio.sentence.id)
            return await get_sentence_by_id(pending_audio.sentence.id)
        else:  
            raise HTTPException(
                status_code=400, 
                detail="The user's sending audio limit is over, please wait for the next sentence"
            )

    # CHECK 2: Find sentences with available slots (optimized aggregation)
    pipeline = [
        {
            "$lookup": {
                "from": "received_audio",
                "localField": "_id",
                "foreignField": "sentence.$id",
                "as": "audios"
            }
        },
        {
            "$addFields": {
                "user_has_audio": {
                    "$in": [user_id, "$audios.user.$id"]
                },
                "active_count": {
                    "$size": {
                        "$filter": {
                            "input": "$audios",
                            "as": "audio",
                            "cond": {
                                "$or": [
                                    {"$eq": ["$$audio.status", "approved"]},
                                    {
                                        "$and": [
                                            {"$eq": ["$$audio.status", "pending"]},
                                            {"$gt": ["$$audio.created_at", timeout_time]}
                                        ]
                                    }
                                ]
                            }
                        }
                    }
                }
            }
        },
        {
            "$match": {
                "user_has_audio": False,
                "active_count": {"$lt": settings.sentence_to_audio_limit}
            }
        },
        {"$sample": {"size": 1}}
    ]

    try:
        results = await Sentence.aggregate(pipeline).to_list()
        if results:
            sentence = await Sentence.get(results[0]["_id"])
            await add_received_audio(user_id, sentence.id)
            logger.info(f"Assigned new sentence {sentence.id} to user {user_id}")
            return sentence
    except Exception as e:
        logger.error(f"Error in sentence aggregation: {str(e)}")

    # CHECK 3: Find pending timeout from other users
    pipeline_pending = [
        {
            "$lookup": {
                "from": "received_audio",
                "localField": "_id",
                "foreignField": "sentence.$id",
                "as": "audios"
            }
        },
        {"$unwind": "$audios"},
        {
            "$match": {
                "audios.user.$id": {"$ne": user_id},
                "audios.status": "pending",
                "audios.created_at": {"$lt": timeout_time}
            }
        },
        {"$sample": {"size": 1}}
    ]
    
    try:
        results_pending = await Sentence.aggregate(pipeline_pending).to_list()
        if results_pending:
            sentence = await Sentence.get(results_pending[0]["_id"])
            received_audio_id = results_pending[0]["audios"]["_id"]
            await update_received_audio_to_newUser(user_id, received_audio_id)
            logger.info(f"Reassigned timed-out sentence {sentence.id} to user {user_id}")
            return sentence
    except Exception as e:
        logger.error(f"Error in pending timeout check: {str(e)}")

    # CHECK 4: Own pending timeout
    pending_own = await ReceivedAudio.find_one(
        ReceivedAudio.user.id == user_id,
        ReceivedAudio.status == AudioStatus.pending,
        ReceivedAudio.created_at < timeout_time
    )
    if pending_own:
        await update_received_audio_reassign_to_thisUser(user_id, pending_own.sentence.id)
        logger.info(f"Reassigned own timed-out sentence {pending_own.sentence.id} to user {user_id}")
        return await get_sentence_by_id(pending_own.sentence.id)

    logger.warning(f"No available sentence found for user {user_id}")
    raise HTTPException(status_code=404, detail="No available sentence found")

async def get_sentence_by_id(sentence_id: PydanticObjectId) -> Sentence:
    """Get sentence by ID with error handling"""
    sentence = await Sentence.get(sentence_id)
    if not sentence:
        raise HTTPException(status_code=404, detail="Sentence not found")
    return sentence
