from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, Query
from app.models.admin_users import AdminUser
from app.schemas.admin_users import AdminUserCreate, AdminUserUpdate
from app.services.admin_user_service import create_admin_user, update_admin_user, get_current_admin_user, get_current_superadmin_user, get_admin_user_by_id, get_all_audios, delete_admin_user, get_all_checked_audios
from app.services.user_service import update_user, delete_user
from app.models.user import User
from app.schemas.user import UserCreate
from app.models.sentence import Sentence
from app.schemas.sentence import SentenceCreate
from app.models.received_audio import AudioStatus, ReceivedAudio
from app.schemas.received_audio import ReceivedAudioOutPut
from app.models.checked_audio import CheckedAudio
from app.services.received_audio_services import get_received_audio_by_id
from typing import Optional, List
from app.core.logging import get_logger

logger = get_logger("api.admin")
router = APIRouter(prefix="/admin", tags=["Admin"])

"""  ==================== Admin User API  =========================== """
@router.get("/admin-users", dependencies=[Depends(get_current_admin_user)])
async def get_admin_users(page: int = Query(1, ge=1), limit: int = Query(10, ge=1)):
    users = await AdminUser.find_all().skip((page - 1) * limit).limit(limit).to_list()
    return [
        {
            "id": str(u.id),
            "username": u.username,
            "is_active": u.is_active,
            "role": u.role,
            "created_at": u.created_at.isoformat(),
            "updated_at": u.updated_at.isoformat()
        }
        for u in users
    ]

@router.post("/", dependencies=[Depends(get_current_superadmin_user)])
async def create_admin_user_api(user: AdminUserCreate):
    new_user = await create_admin_user(user)
    return {
        "id": str(new_user.id),
        "username": new_user.username,
        "is_active": new_user.is_active,
        "role": new_user.role,
        "created_at": new_user.created_at.isoformat(),
        "updated_at": new_user.updated_at.isoformat()
    }

@router.put("/{id}", dependencies=[Depends(get_current_superadmin_user)])
async def update_admin_user_by_id_api(id: PydanticObjectId, user_data: AdminUserUpdate):
    user = await update_admin_user(id, user_data)
    return {
        "id": str(user.id),
        "username": user.username,
        "is_active": user.is_active,
        "role": user.role,
        "created_at": user.created_at.isoformat(),
        "updated_at": user.updated_at.isoformat()
    }

@router.delete("/{id}", dependencies=[Depends(get_current_superadmin_user)])
async def delete_admin_user_by_id_api(id: PydanticObjectId):
    await delete_admin_user(id)
    return {"message": "Admin user deleted successfully"}


#  ==================== User API  ===========================
@router.get("/users", dependencies=[Depends(get_current_admin_user)])
async def get_users(page: int = Query(1, ge=1), limit: int = Query(10, ge=1), name: Optional[str] = Query(None)):
    query = {}
    if name:
        query["name"] = {"$regex": name, "$options": "i"}
    users = await User.find(query).skip((page - 1) * limit).limit(limit).to_list()
    return [
        {
            "id": str(u.id),
            "telegram_id": u.telegram_id,
            "name": u.name,
            "gender": u.gender,
            "age": u.age,
            "info": u.info,
            "created_at": u.created_at.isoformat()
        }
        for u in users
    ]

@router.put("/users/{id}", dependencies=[Depends(get_current_admin_user)])
async def update_user_by_id_to_admin(id: PydanticObjectId, user_data: UserCreate):
    user = await update_user(id, user_data)
    return {
        "id": str(user.id),
        "telegram_id": user.telegram_id,
        "name": user.name,
        "gender": user.gender,
        "age": user.age,
        "info": user.info,
        "created_at": user.created_at.isoformat()
    }

@router.delete("/users/{id}", dependencies=[Depends(get_current_admin_user)])
async def delete_user_by_id_api(id: PydanticObjectId):
    await delete_user(id)
    return {"message": "User deleted successfully"}

# ======================= Sentence API ===========================
@router.get("/sentences", dependencies=[Depends(get_current_admin_user)])
async def get_sentences(page: int = Query(1, ge=1), limit: int = Query(10, ge=1), text: Optional[str] = Query(None)):
    query = {}
    if text:
        query["text"] = {"$regex": text, "$options": "i"}
    sentences = await Sentence.find(query).skip((page - 1) * limit).limit(limit).to_list()
    return [
        {
            "id": str(s.id),
            "text": s.text,
            "language": s.language,
            "created_at": s.created_at.isoformat()
        }
        for s in sentences
    ]

# ======================= Received Audio API ===========================
@router.get("/audios", dependencies=[Depends(get_current_admin_user)])
async def get_audios_api(
    page: int = Query(1, ge=1), 
    limit: int = Query(20, ge=1),
    status: Optional[str] = Query(None, description="Filter by status: pending or approved"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    sentence_id: Optional[str] = Query(None, description="Filter by sentence ID")
):
    """Get all received audios with pagination and filters"""
    return await get_all_audios(page, limit)

@router.get("/audios/{id}", dependencies=[Depends(get_current_admin_user)])
async def get_audio_by_id_api(id: PydanticObjectId):
    """Get single audio by ID"""
    audio = await get_received_audio_by_id(id)
    
    # Fetch links
    await audio.fetch_all_links()
    
    return {
        "id": str(audio.id),
        "audio_path": audio.audio_path,
        "duration": audio.duration,
        "status": audio.status,
        "created_at": audio.created_at.isoformat() if audio.created_at else None,
        "sentence": audio.sentence.text if audio.sentence else None,
        "sentence_id": str(audio.sentence.id) if audio.sentence else None,
        "user_name": audio.user.name if audio.user else None,
        "user_id": str(audio.user.id) if audio.user else None,
        "user_telegram_id": audio.user.telegram_id if audio.user else None,
        "user_gender": audio.user.gender if audio.user else None,
        "user_age": audio.user.age if audio.user else None
    }

@router.put("/audios/{id}", dependencies=[Depends(get_current_admin_user)])
async def update_received_audio_by_id_api(id: PydanticObjectId, received_audio_data: ReceivedAudioOutPut):
    audio = await get_received_audio_by_id(id)
    if received_audio_data.status:
        audio.status = received_audio_data.status
    if received_audio_data.audio_path:
        audio.audio_path = received_audio_data.audio_path
    
    # Update links
    audio.sentence = received_audio_data.sentence_id
    audio.user = received_audio_data.user_id
    
    await audio.save()
    return {
        "id": str(audio.id),
        "user_id": str(audio.user.id) if audio.user else None,
        "sentence_id": str(audio.sentence.id) if audio.sentence else None,
        "audio_path": audio.audio_path,
        "duration": audio.duration,
        "status": audio.status,
        "created_at": audio.created_at.isoformat()
    }

@router.delete("/audios/{id}", dependencies=[Depends(get_current_admin_user)])
async def delete_audio_by_id_api(id: PydanticObjectId):
    """Delete audio by ID"""
    audio = await get_received_audio_by_id(id)
    
    # Check if audio has been checked
    checked = await CheckedAudio.find_one(CheckedAudio.audio.id == id)
    if checked:
        raise HTTPException(
            status_code=400, 
            detail="Cannot delete audio that has been checked"
        )
    
    # Delete audio file if exists
    if audio.audio_path:
        import os
        from app.config import MEDIA_DIR
        file_path = os.path.join(MEDIA_DIR, audio.audio_path)
        if os.path.exists(file_path):
            os.remove(file_path)
    
    await audio.delete()
    return {"message": "Audio deleted successfully", "id": str(id)}

# ======================= Checked Audio API ===========================
@router.get("/checked-audios", dependencies=[Depends(get_current_admin_user)])
async def get_checked_audios_api(
    page: int = Query(1, ge=1), 
    limit: int = Query(20, ge=1),
    status: Optional[str] = Query(None, description="Filter by status"),
    is_correct: Optional[bool] = Query(None, description="Filter by is_correct"),
    checked_by_id: Optional[str] = Query(None, description="Filter by checker ID")
):
    """Get all checked audios with pagination and filters"""
    return await get_all_checked_audios(page, limit)

@router.get("/checked-audios/{id}", dependencies=[Depends(get_current_admin_user)])
async def get_checked_audio_by_id_api(id: PydanticObjectId):
    """Get single checked audio by ID"""
    from app.services.checked_audio_services import get_checked_audio_by_id
    
    ca = await get_checked_audio_by_id(id)
    await ca.fetch_all_links()
    
    # Get audio details
    audio_path = None
    audio_duration = None
    sentence_text = None
    sentence_id = None
    user_name = None
    user_id = None
    
    if ca.audio:
        audio_path = ca.audio.audio_path
        audio_duration = ca.audio.duration
        if ca.audio.sentence:
            sentence_text = ca.audio.sentence.text
            sentence_id = str(ca.audio.sentence.id)
        if ca.audio.user:
            user_name = ca.audio.user.name
            user_id = str(ca.audio.user.id)
    
    return {
        "id": str(ca.id),
        "audio_id": str(ca.audio.id) if ca.audio else None,
        "audio_path": audio_path,
        "audio_duration": audio_duration,
        "sentence": sentence_text,
        "sentence_id": sentence_id,
        "user_name": user_name,
        "user_id": user_id,
        "checked_by_id": str(ca.checked_by.id) if ca.checked_by else None,
        "checked_by_name": ca.checked_by.username if ca.checked_by else None,
        "comment": ca.comment,
        "is_correct": ca.is_correct,
        "status": ca.status,
        "checked_at": ca.checked_at.isoformat() if ca.checked_at else None,
        "second_checker_id": str(ca.second_checker.id) if ca.second_checker else None,
        "second_check_result": ca.second_check_result,
        "second_checked_at": ca.second_checked_at.isoformat() if ca.second_checked_at else None
    }

@router.delete("/checked-audios/{id}", dependencies=[Depends(get_current_admin_user)])
async def delete_checked_audio_by_id_api(id: PydanticObjectId):
    """Delete checked audio by ID"""
    from app.services.checked_audio_services import get_checked_audio_by_id
    
    ca = await get_checked_audio_by_id(id)
    await ca.delete()
    return {"message": "Checked audio deleted successfully", "id": str(id)}

# ======================= Statistics API ===========================
@router.get("/statistics", dependencies=[Depends(get_current_admin_user)])
async def get_admin_statistics(current_user: dict = Depends(get_current_admin_user)):
    # Basic counts
    users_count = await User.count()
    sentences_count = await Sentence.count()
    audios_count = await ReceivedAudio.count()
    approved_audios_count = await ReceivedAudio.find(ReceivedAudio.status == AudioStatus.approved).count()
    pending_audios_count = await ReceivedAudio.find(ReceivedAudio.status == AudioStatus.pending).count()
    checked_audios_count = await CheckedAudio.count()
    admins_count = await AdminUser.count()
    
    # Duration aggregate
    pipeline_dur = [
        {"$match": {"status": "approved"}},
        {"$group": {"_id": None, "total": {"$sum": "$duration"}}}
    ]
    duration_res = await ReceivedAudio.aggregate(pipeline_dur).to_list()
    total_audio_duration = duration_res[0]["total"] if duration_res else 0
    
    statistics = {
        "users": users_count,
        "sentences": sentences_count,
        "audios": audios_count,
        "approved_audios": approved_audios_count,
        "pending_audios": pending_audios_count,
        "checked_audios": checked_audios_count,
        "admins": admins_count,
        "total_audio_duration": round(total_audio_duration / 60, 2) if total_audio_duration else 0,
        "total_audio_duration_minutes": round(total_audio_duration / 60, 2) if total_audio_duration else 0,
        "total_audio_duration_hours": round(total_audio_duration / 3600, 2) if total_audio_duration else 0
    }

    # Samples for the dashboard - use simple list format for statistics
    users = await User.find_all().sort(-User.created_at).limit(20).to_list()
    sentences = await Sentence.find_all().sort(-Sentence.created_at).limit(20).to_list()
    
    # Get audios without pagination wrapper for statistics
    audios_list = await ReceivedAudio.find_all(fetch_links=True).sort(-ReceivedAudio.created_at).limit(20).to_list()
    formatted_audios = []
    for a in audios_list:
        formatted_audios.append({
            "id": str(a.id),
            "audio_path": a.audio_path,
            "duration": a.duration,
            "status": a.status,
            "created_at": a.created_at.isoformat() if a.created_at else None,
            "sentence": a.sentence.text if a.sentence else None,
            "sentence_id": str(a.sentence.id) if a.sentence else None,
            "user_name": a.user.name if a.user else None,
            "user_id": str(a.user.id) if a.user else None
        })
    
    # Get checked audios without pagination wrapper for statistics
    checked_audios_list = await CheckedAudio.find_all(fetch_links=True).sort(-CheckedAudio.checked_at).limit(20).to_list()
    formatted_checked_audios = []
    for ca in checked_audios_list:
        audio_path = None
        audio_duration = None
        sentence_text = None
        sentence_id = None
        user_name = None
        user_id = None

        try:
            if ca.audio:
                audio_path = ca.audio.audio_path
                audio_duration = ca.audio.duration
                if ca.audio.sentence:
                    sentence_text = ca.audio.sentence.text
                    sentence_id = str(ca.audio.sentence.id)
                if ca.audio.user:
                    user_name = ca.audio.user.name
                    user_id = str(ca.audio.user.id)
        except Exception:
            pass

        checked_by_id = None
        checked_by_name = None
        try:
            if ca.checked_by:
                checked_by_id = str(ca.checked_by.id)
                checked_by_name = ca.checked_by.name  # User.name
        except Exception:
            pass

        second_checker_id = None
        second_checker_name = None
        try:
            if ca.second_checker:
                second_checker_id = str(ca.second_checker.id)
                second_checker_name = ca.second_checker.username  # AdminUser.username
        except Exception:
            pass

        formatted_checked_audios.append({
            "id": str(ca.id),
            "audio_id": str(ca.audio.id) if ca.audio else None,
            "audio_path": audio_path,
            "audio_duration": audio_duration,
            "sentence": sentence_text,
            "sentence_id": sentence_id,
            "user_name": user_name,
            "user_id": user_id,
            "checked_by": checked_by_id,
            "checked_by_name": checked_by_name,
            "comment": ca.comment,
            "is_correct": ca.is_correct,
            "status": ca.status,
            "checked_at": ca.checked_at.isoformat() if ca.checked_at else None,
            "second_checker_id": second_checker_id,
            "second_checker_name": second_checker_name,
            "second_check_result": ca.second_check_result,
            "second_checked_at": ca.second_checked_at.isoformat() if ca.second_checked_at else None
        })
    
    admins = await AdminUser.find_all().sort(-AdminUser.created_at).limit(20).to_list()

    # Format users
    formatted_users = []
    for u in users:
        formatted_users.append({
            "id": str(u.id),
            "telegram_id": u.telegram_id,
            "name": u.name,
            "gender": u.gender,
            "age": u.age,
            "info": u.info,
            "created_at": u.created_at.isoformat()
        })

    # Format sentences
    formatted_sentences = []
    for s in sentences:
        formatted_sentences.append({
            "id": str(s.id),
            "text": s.text,
            "language": s.language,
            "created_at": s.created_at.isoformat()
        })

    # Format admins
    formatted_admins = []
    for a in admins:
        formatted_admins.append({
            "id": str(a.id),
            "username": a.username,
            "is_active": a.is_active,
            "role": a.role,
            "created_at": a.created_at.isoformat(),
            "updated_at": a.updated_at.isoformat()
        })

    return {
        "users": formatted_users,
        "sentences": formatted_sentences,
        "audios": formatted_audios,
        "checked_audios": formatted_checked_audios,
        "admin_users": formatted_admins,
        "current_admin": current_user,
        "statistics": statistics
    }
