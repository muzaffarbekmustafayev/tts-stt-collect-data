from fastapi import APIRouter, HTTPException
from app.models.user import User
from app.schemas.user import UserCreate
from app.core.logging import get_logger
from app.services.user_service import get_user_by_userId, get_user_by_telegramId, create_user, update_user, delete_user
from beanie import PydanticObjectId

logger = get_logger("api.user")
router = APIRouter(prefix="/users", tags=["Users"])

# add user
@router.post("/")
async def create_user_endpoint(user: UserCreate):
    new_user = await create_user(user)
    return {
        "id": str(new_user.id),
        "telegram_id": new_user.telegram_id,
        "name": new_user.name,
        "gender": new_user.gender,
        "age": new_user.age,
        "info": new_user.info,
        "created_at": new_user.created_at.isoformat()
    }

# get user by telegram id
@router.get("/{telegram_id}")
async def get_user_by_telegram_id(telegram_id: str):
    user = await get_user_by_telegramId(telegram_id)
    return {
        "id": str(user.id),
        "telegram_id": user.telegram_id,
        "name": user.name,
        "gender": user.gender,
        "age": user.age,
        "info": user.info,
        "created_at": user.created_at.isoformat()
    }
  
# get user by id
@router.get("/by-id/{id}")
async def get_user_by_id(id: str):
    # Validate ObjectId
    if not id or id == "undefined" or id == "null":
        raise HTTPException(status_code=400, detail="Invalid user ID")
    
    try:
        object_id = PydanticObjectId(id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user ID format")
    
    user = await get_user_by_userId(object_id)
    return {
        "id": str(user.id),
        "telegram_id": user.telegram_id,
        "name": user.name,
        "gender": user.gender,
        "age": user.age,
        "info": user.info,
        "created_at": user.created_at.isoformat()
    }

# update user
@router.put("/{id}")
async def update_user_by_id(id: str, user_data: UserCreate):
    # Validate ObjectId
    if not id or id == "undefined" or id == "null":
        raise HTTPException(status_code=400, detail="Invalid user ID")
    
    try:
        object_id = PydanticObjectId(id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user ID format")
    
    user = await update_user(object_id, user_data)
    return {
        "id": str(user.id),
        "telegram_id": user.telegram_id,
        "name": user.name,
        "gender": user.gender,
        "age": user.age,
        "info": user.info,
        "created_at": user.created_at.isoformat()
    }
