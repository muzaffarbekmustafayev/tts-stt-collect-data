from beanie import PydanticObjectId
from fastapi import HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta, UTC
from typing import Optional

from app.models.admin_users import AdminUser
from app.schemas.admin_users import AdminUserCreate, AdminUserUpdate
from app.models.received_audio import ReceivedAudio
from app.models.checked_audio import CheckedAudio
from app.config import settings

# Config
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", scheme_name="Bearer")

async def get_admin_user_by_id(id: PydanticObjectId) -> AdminUser | None:
    user = await AdminUser.get(id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

async def get_admin_user_by_username(username: str) -> AdminUser | None:
    user = await AdminUser.find_one(AdminUser.username == username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

async def create_admin_user(user_data: AdminUserCreate) -> AdminUser:
    username = user_data.username.strip()
    if len(username) < 3 or len(username) > 50:
        raise HTTPException(status_code=400, detail="Username must be between 3 and 50 characters long")
    
    existing = await AdminUser.find_one(AdminUser.username == username)
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    if len(user_data.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters long")
    
    hashed_pass = hash_password(user_data.password)
    new_user = AdminUser(
        username=username,
        password=hashed_pass,
        role=user_data.role,
        is_active=user_data.is_active
    )
    await new_user.insert()
    return new_user

async def update_admin_user(id: PydanticObjectId, user_data: AdminUserUpdate) -> AdminUser:
    admin = await get_admin_user_by_id(id)
    
    username = user_data.username.strip()
    if len(username) < 3 or len(username) > 50:
        raise HTTPException(status_code=400, detail="Username must be between 3 and 50 characters long")
    
    existing = await AdminUser.find_one(AdminUser.username == username, AdminUser.id != id)
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    if user_data.password:
        if len(user_data.password) < 8:
            raise HTTPException(status_code=400, detail="Password must be at least 8 characters long")
        admin.password = hash_password(user_data.password)
        
    admin.username = username
    admin.role = user_data.role
    admin.is_active = user_data.is_active
    admin.updated_at = datetime.now(UTC)
    await admin.save()
    return admin

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token not valid",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = await get_admin_user_by_username(username)
    return {"id": user.id, "username": user.username, "role": user.role, "is_active": user.is_active}


def get_current_admin_user(current_user: dict = Depends(get_current_user)):
    if current_user["role"].lower() != "admin" and current_user["role"].lower() != "superadmin" and current_user["is_active"] == False:
        raise HTTPException(status_code=403, detail="You don't have permission to access this resource")
    return current_user

def get_current_checker_user(current_user: dict = Depends(get_current_user)):
    if current_user["role"].lower() not in ["checker", "admin", "superadmin"] and current_user["is_active"] == False:
        raise HTTPException(status_code=403, detail="You don't have permission to access this resource")
    return current_user

def get_current_superadmin_user(current_user: dict = Depends(get_current_user)):
    if current_user["role"].lower() != "superadmin":
        raise HTTPException(status_code=403, detail="You don't have permission to access this resource")
    return current_user


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.now(UTC) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def hash_password(password: str):
    return pwd_context.hash(password)


def get_payload(token: str):
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    return payload

async def get_all_audios(page: int, limit: int):
    # Beanie aggregation or find with skip/limit and fetch links
    audios = await ReceivedAudio.find_all(fetch_links=True).sort(-ReceivedAudio.created_at).skip((page - 1) * limit).limit(limit).to_list()
    
    # Get total count for pagination
    total = await ReceivedAudio.count()
    
    # Formatting for output
    formatted = []
    for a in audios:
        formatted.append({
            "id": str(a.id),
            "audio_path": a.audio_path,
            "duration": a.duration,
            "status": a.status,
            "created_at": a.created_at.isoformat() if a.created_at else None,
            "sentence": a.sentence.text if a.sentence else None,
            "sentence_id": str(a.sentence.id) if a.sentence else None,
            "user_name": a.user.name if a.user else None,
            "user_id": str(a.user.id) if a.user else None,
            "user_telegram_id": a.user.telegram_id if a.user else None,
            "user_gender": a.user.gender if a.user else None,
            "user_age": a.user.age if a.user else None
        })
    
    return {
        "data": formatted,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit
    }

async def get_all_checked_audios(page: int, limit: int):
    checked_audios = await CheckedAudio.find_all(fetch_links=True).sort(-CheckedAudio.checked_at).skip((page - 1) * limit).limit(limit).to_list()
    
    total = await CheckedAudio.count()
    
    formatted = []
    for ca in checked_audios:
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

        # checked_by is Link[User] - User has 'name', not 'username'
        checked_by_id = None
        checked_by_name = None
        try:
            if ca.checked_by:
                checked_by_id = str(ca.checked_by.id)
                checked_by_name = ca.checked_by.name  # User.name (not username)
        except Exception:
            pass

        # second_checker is Link[AdminUser] - AdminUser has 'username'
        second_checker_id = None
        second_checker_name = None
        try:
            if ca.second_checker:
                second_checker_id = str(ca.second_checker.id)
                second_checker_name = ca.second_checker.username
        except Exception:
            pass

        formatted.append({
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
    
    return {
        "data": formatted,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit
    }

async def delete_admin_user(id: PydanticObjectId) -> AdminUser:
    admin_user = await get_admin_user_by_id(id)
    await admin_user.delete()
    return admin_user