from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserOut
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from app.core.logging import get_logger
from app.services.admin_user_service import get_admin_user_by_id, get_admin_user_by_username, create_admin_user, update_admin_user
from app.models.admin_users import AdminUser
from app.schemas.admin_users import AdminUserCreate, AdminUserOut

logger = get_logger("api.user")
router = APIRouter(prefix="/admin", tags=["Admin"])

# add user
@router.post("/", response_model=AdminUserOut)
async def create_admin_user(user: AdminUserCreate, db: AsyncSession = Depends(get_db)):
    new_user = await create_admin_user(user, db)
    return new_user

# get user by telegram id
@router.get("/{username}", response_model=AdminUserOut)
async def get_admin_user_by_username(username: str, db: AsyncSession = Depends(get_db)):
    user = await get_admin_user_by_username(username, db)
    return user
  
# get user by id
@router.get("/by-id/{id}", response_model=AdminUserOut)
async def get_admin_user_by_id(id: int, db: AsyncSession = Depends(get_db)):
    user = await get_admin_user_by_id(id, db)
    return user
  
# get all users
@router.get("/", response_model=list[AdminUserOut])
async def get_all_admin_users(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AdminUser))
    users = result.scalars().all()
    logger.info(f"Found {len(users)} users")
    return users
  
# update user
@router.put("/{id}", response_model=AdminUserOut)
async def update_admin_user_by_id(id: int, user_data: AdminUserCreate, db: AsyncSession = Depends(get_db)):
    user = await update_admin_user(id, user_data, db)
    return user
