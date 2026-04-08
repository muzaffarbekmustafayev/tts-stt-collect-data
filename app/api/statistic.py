from beanie import PydanticObjectId
from fastapi import APIRouter, HTTPException, Query
from app.models.user import User
from app.models.sentence import Sentence
from app.models.received_audio import ReceivedAudio, AudioStatus
from app.models.checked_audio import CheckedAudio
from app.core.logging import get_logger
from typing import Optional, List

logger = get_logger("api.statistic")
router = APIRouter(prefix="/statistic", tags=["Statistic"])

@router.get("/")
async def get_statistic():
    users_count = await User.count()
    sentences_count = await Sentence.count()
    audios_count = await ReceivedAudio.find(ReceivedAudio.status == AudioStatus.approved).count()
    checked_audios_count = await CheckedAudio.find(CheckedAudio.status == AudioStatus.approved).count()
    
    # Aggregation for total duration
    pipeline = [
        {"$match": {"status": "approved"}},
        {"$group": {"_id": None, "total": {"$sum": "$duration"}}}
    ]
    duration_res = await ReceivedAudio.aggregate(pipeline).to_list()
    total_audio_duration = duration_res[0]["total"] if duration_res else 0
    
    return {
        "users": users_count,
        "sentences": sentences_count,
        "audios": audios_count,
        "checked_audios": checked_audios_count,
        "total_audio_duration": total_audio_duration / 60 if total_audio_duration else 0
    }


@router.get("/by-users")
async def get_statistic_by_users(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1),
    name: Optional[str] = Query(None, description="User name bo'yicha qidirish")
):
    """Get statistics by users with pagination"""
    # MongoDB Aggregation for per-user statistics
    match_stage = {}
    if name:
        match_stage = {"name": {"$regex": name, "$options": "i"}}

    pipeline = [
        {"$match": match_stage} if match_stage else {"$match": {}},
        {"$lookup": {
            "from": "received_audio",
            "localField": "_id",
            "foreignField": "user.$id",
            "as": "sent_audios"
        }},
        {"$lookup": {
            "from": "checked_audio",
            "localField": "_id",
            "foreignField": "checked_by.$id",
            "as": "checked_audios"
        }},
        {"$addFields": {
            "sent_audio_count": {
                "$size": {"$filter": {
                    "input": "$sent_audios",
                    "as": "s",
                    "cond": {"$eq": ["$$s.status", "approved"]}
                }}
            },
            "sent_duration_seconds": {
                "$sum": {
                    "$map": {
                        "input": {"$filter": {
                            "input": "$sent_audios",
                            "as": "s",
                            "cond": {"$eq": ["$$s.status", "approved"]}
                        }},
                        "as": "s",
                        "in": {"$ifNull": ["$$s.duration", 0]}
                    }
                }
            },
            "pending_audio_count": {
                "$size": {"$filter": {
                    "input": "$sent_audios",
                    "as": "s",
                    "cond": {"$eq": ["$$s.status", "pending"]}
                }}
            },
            "checked_audio_count": {
                "$size": {"$filter": {
                    "input": "$checked_audios",
                    "as": "c",
                    "cond": {"$eq": ["$$c.status", "approved"]}
                }}
            },
            "pending_checked_audio_count": {
                "$size": {"$filter": {
                    "input": "$checked_audios",
                    "as": "c",
                    "cond": {"$eq": ["$$c.status", "pending"]}
                }}
            }
        }},
        {"$sort": {"_id": 1}},
        {"$skip": (page - 1) * limit},
        {"$limit": limit}
    ]

    results = await User.aggregate(pipeline).to_list()
    
    users_statistics = []
    for row in results:
        sent_duration_sec = row.get("sent_duration_seconds", 0) or 0
        
        users_statistics.append({
            "user_id": str(row["_id"]),
            "name": row.get("name", ""),
            "telegram_id": row.get("telegram_id"),
            "info": row.get("info"),
            "sent_audio_count": row.get("sent_audio_count", 0),
            "sent_audio_minutes": round(sent_duration_sec / 60, 2) if sent_duration_sec else 0.0,
            "checked_audio_count": row.get("checked_audio_count", 0),
            "checked_audio_minutes": 0.0,
            "pending_audio_count": row.get("pending_audio_count", 0),
            "pending_checked_audio_count": row.get("pending_checked_audio_count", 0)
        })
    
    return users_statistics


@router.get("/by-users/audios")
async def get_audios_by_users(
    user_id: Optional[PydanticObjectId] = Query(None, description="User ID orqali qidirish"),
    telegram_id: Optional[str] = Query(None, description="Telegram ID orqali qidirish")
):
    """Get user's audios by user_id or telegram_id"""
    if not user_id and not telegram_id:
        raise HTTPException(status_code=400, detail="user_id yoki telegram_id kamida bittasi kerak")
    
    user = None
    if user_id:
        user = await User.get(user_id)
    elif telegram_id:
        user = await User.find_one(User.telegram_id == telegram_id)
        
    if not user:
        raise HTTPException(status_code=404, detail="User topilmadi")
    
    # Sent audios
    sent_audios_list = await ReceivedAudio.find(
        ReceivedAudio.user == user.id,
        ReceivedAudio.status == AudioStatus.approved,
        fetch_links=True
    ).sort(-ReceivedAudio.created_at).to_list()

    sent_audios = []
    for ra in sent_audios_list:
        sent_audios.append({
            "id": str(ra.id),
            "sentence_id": str(ra.sentence.id) if ra.sentence else None,
            "sentence": ra.sentence.text if ra.sentence else None,
            "audio_path": ra.audio_path,
            "duration": ra.duration,
            "status": ra.status,
            "created_at": ra.created_at.isoformat()
        })

    # Checked audios
    checked_audios_list = await CheckedAudio.find(
        CheckedAudio.checked_by == user.id,
        CheckedAudio.status == AudioStatus.approved,
        fetch_links=True
    ).sort(-CheckedAudio.checked_at).to_list()
    
    checked_audios = []
    for ca in checked_audios_list:
        ra = ca.audio
        checked_audios.append({
            "id": str(ca.id),
            "audio_id": str(ra.id) if ra else None,
            "sentence_id": str(ra.sentence.id) if ra and ra.sentence else None,
            "sentence": ra.sentence.text if ra and ra.sentence else None,
            "audio_path": ra.audio_path if ra else None,
            "duration": ra.duration if ra else None,
            "is_correct": ca.is_correct,
            "comment": ca.comment,
            "status": ca.status,
            "checked_at": ca.checked_at.isoformat()
        })
    
    return {
        "user_id": str(user.id),
        "name": user.name,
        "telegram_id": user.telegram_id,
        "sent_audios": sent_audios,
        "checked_audios": checked_audios,
        "sent_audios_count": len(sent_audios),
        "checked_audios_count": len(checked_audios)
    }
