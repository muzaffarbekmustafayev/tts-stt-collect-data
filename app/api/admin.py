from fastapi import APIRouter, Depends, Request, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from sqlalchemy import select, func, text
from app.core.logging import get_logger
from app.models.admin_users import AdminUser
from app.schemas.admin_users import AdminUserCreate, AdminUserOut
from app.services.admin_user_service import create_admin_user, update_admin_user, get_current_admin_user, get_current_superadmin_user, get_admin_user_by_id
from app.services.user_service import update_user, delete_user
from app.models.user import User
from app.schemas.user import UserOut, UserCreate
from app.models.sentence import Sentence
from app.schemas.sentence import SentenceOut
from app.models.received_audio import ReceivedAudio
from app.schemas.received_audio import ReceivedAudioOut
from app.models.checked_audio import CheckedAudio
from app.schemas.checked_audio import CheckedAudioOut

logger = get_logger("api.admin")
router = APIRouter(prefix="/admin", tags=["Admin"])

"""  ==================== Admin User API  =========================== """
# get admin users
@router.get("/admin-users", response_model=list[AdminUserOut], dependencies=[Depends(get_current_admin_user)])
async def get_admin_users(page: int = Query(1, ge=1), limit: int = Query(10, ge=1), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AdminUser).offset((page - 1) * limit).limit(limit))
    users = result.scalars().all()
    return users

# add admin user
@router.post("/", response_model=AdminUserOut, dependencies=[Depends(get_current_superadmin_user)])
async def create_admin_user_api(user: AdminUserCreate, db: AsyncSession = Depends(get_db)):
    new_user = await create_admin_user(user, db)
    return new_user

# update admin user
@router.put("/{id}", response_model=AdminUserOut, dependencies=[Depends(get_current_superadmin_user)])
async def update_admin_user_by_id_api(id: int, user_data: AdminUserCreate, db: AsyncSession = Depends(get_db)):
    user = await update_admin_user(id, user_data, db)
    return user

# # delete admin user
# @router.delete("/{id}", dependencies=[Depends(get_current_superadmin_user)])
# async def delete_admin_user_by_id_api(id: int, db: AsyncSession = Depends(get_db)):
#     await delete_admin_user(id, db)
#     return {"message": "Admin user deleted successfully"}


#  ==================== User API  ===========================
# get all users
@router.get("/users", response_model=list[UserOut], dependencies=[Depends(get_current_admin_user)])
async def get_users(page: int = Query(1, ge=1), limit: int = Query(10, ge=1), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).offset((page - 1) * limit).limit(limit))
    users = result.scalars().all()
    return users

# update user by id
@router.put("/users/{id}", response_model=UserOut, dependencies=[Depends(get_current_admin_user)])
async def update_user_by_id(id: int, user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    redirect_url = f"/users/{id}"
    return RedirectResponse(url=redirect_url, status_code=303)

# delete user by id
@router.delete("/users/{id}", dependencies=[Depends(get_current_admin_user)])
async def delete_user_by_id(id: int, db: AsyncSession = Depends(get_db)):
    await delete_user(id, db)
    return {"message": "User deleted successfully"}

# ======================= Sentence API ===========================
#get sentences
@router.get("/sentences", response_model=list[SentenceOut], dependencies=[Depends(get_current_admin_user)])
async def get_sentences(page: int = Query(1, ge=1), limit: int = Query(10, ge=1), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Sentence).offset((page - 1) * limit).limit(limit))
    sentences = result.scalars().all()
    return sentences

# ======================= Received Audio API ===========================
#get audios
@router.get("/audios", response_model=list[ReceivedAudioOut], dependencies=[Depends(get_current_admin_user)])
async def get_audios(page: int = Query(1, ge=1), limit: int = Query(10, ge=1), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ReceivedAudio).offset((page - 1) * limit).limit(limit))
    audios = result.scalars().all()
    return audios

# ======================= Checked Audio API ===========================
#get checked audios
@router.get("/checked-audios", response_model=list[CheckedAudioOut], dependencies=[Depends(get_current_admin_user)])
async def get_checked_audios(page: int = Query(1, ge=1), limit: int = Query(10, ge=1), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(CheckedAudio).offset((page - 1) * limit).limit(limit))
    checked_audios = result.scalars().all()
    return checked_audios

# ======================= Statistics API ===========================
@router.get("/statistics", response_model=dict, dependencies=[Depends(get_current_admin_user)])
async def get_admin_statistics(db: AsyncSession = Depends(get_db)):
    stmt = text("""
        WITH user_count AS (SELECT COUNT(*) as count FROM users),
             sentence_count AS (SELECT COUNT(*) as count FROM sentences),
             audio_count AS (SELECT COUNT(*) as count FROM received_audio),
             checked_audio_count AS (SELECT COUNT(*) as count FROM checked_audio),
             admin_count AS (SELECT COUNT(*) as count FROM admin_users)
        SELECT 
            (SELECT count FROM user_count) as users,
            (SELECT count FROM sentence_count) as sentences,
            (SELECT count FROM audio_count) as audios,
            (SELECT count FROM checked_audio_count) as checked_audios,
            (SELECT count FROM admin_count) as admins
    """)
    result = await db.execute(stmt)
    row_data = result.first()
    statistics = {
        "users": row_data.users or 0,
        "sentences": row_data.sentences or 0,
        "audios": row_data.audios or 0,
        "checked_audios": row_data.checked_audios or 0,
        "admins": row_data.admins or 0
    }
    users_result = await db.execute(select(User).limit(10))
    users = users_result.scalars().all()
    sentences_result = await db.execute(select(Sentence).limit(10))
    sentences = sentences_result.scalars().all()
    audios_result = await db.execute(select(ReceivedAudio).limit(10))
    audios = audios_result.scalars().all()
    checked_audios_result = await db.execute(select(CheckedAudio).limit(10))
    checked_audios = checked_audios_result.scalars().all()
    admins_result = await db.execute(select(AdminUser).limit(10))
    admins = admins_result.scalars().all()
    return {
        "users": [UserOut.model_validate(user).model_dump() for user in users],
        "sentences": [SentenceOut.model_validate(sentence).model_dump() for sentence in sentences],
        "audios": [ReceivedAudioOut.model_validate(audio).model_dump() for audio in audios],
        "checked_audios": [CheckedAudioOut.model_validate(audio).model_dump() for audio in checked_audios],
        "admins": [AdminUserOut.model_validate(admin).model_dump() for admin in admins],
        "statistics": statistics
    }
