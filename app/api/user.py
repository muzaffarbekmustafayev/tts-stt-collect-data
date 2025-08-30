from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserOut
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from app.core.logging import get_logger
from app.services.user_service import get_user_by_userId, get_user_by_telegramId, create_user, update_user, delete_user
from app.services.admin_user_service import get_current_admin_user

logger = get_logger("api.user")
router = APIRouter(prefix="/users", tags=["Users"])

# add user
@router.post("/", response_model=UserOut)
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    new_user = await create_user(user, db)
    return new_user

# get user by telegram id
@router.get("/{telegram_id}", response_model=UserOut)
async def get_user_by_telegram_id(telegram_id: str, db: AsyncSession = Depends(get_db)):
    user = await get_user_by_telegramId(telegram_id, db)
    return user
  
# get user by id
@router.get("/by-id/{id}", response_model=UserOut)
async def get_user_by_id(id: int, db: AsyncSession = Depends(get_db)):
    user = await get_user_by_userId(id, db)
    return user

# update user
@router.put("/{id}", response_model=UserOut)
async def update_user_by_id(id: int, user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    user = await update_user(id, user_data, db)
    return user
