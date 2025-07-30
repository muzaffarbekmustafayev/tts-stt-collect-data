from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserOut
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from app.core.logging import get_logger
from app.services.user_service import get_user_by_userId, get_user_by_telegramId

logger = get_logger("api.user")
router = APIRouter(prefix="/users", tags=["Users"])

# add user
@router.post("/", response_model=UserOut)
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    new_user = User(**user.model_dump())
    db.add(new_user)
    try:
        await db.commit()
        await db.refresh(new_user)
        logger.info(f"User created successfully with ID: {new_user.id}")
        return new_user
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="User already exists")

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
  
# get all users
@router.get("/", response_model=list[UserOut])
async def get_all_users(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User))
    users = result.scalars().all()
    logger.info(f"Found {len(users)} users")
    return users
  
# update user
@router.put("/{id}", response_model=UserOut)
async def update_user(id: int, user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    db_user = await get_user_by_userId(id, db)
    
    # Update user fields
    db_user.telegram_id = user_data.telegram_id
    db_user.name = user_data.name
    db_user.gender = user_data.gender
    db_user.age = user_data.age
    db_user.info = user_data.info
    
    await db.commit()
    await db.refresh(db_user)
    logger.info(f"User updated successfully with ID: {db_user.id}")
    return db_user
