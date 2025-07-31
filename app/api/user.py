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
    if new_user.age < 1 or new_user.age > 120:
        raise HTTPException(status_code=400, detail="Age must be between 1 and 120")
    if new_user.gender.lower() not in ["male", "female"]:
        raise HTTPException(status_code=400, detail="Gender must be either male or female")
    if len(new_user.name) < 3 or len(new_user.name) > 100:
        raise HTTPException(status_code=400, detail="Name must be between 3 and 100 characters")
    if len(new_user.info) > 500:
        raise HTTPException(status_code=400, detail="Info must be less than 500 characters")
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
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    if user_data.age and (user_data.age < 1 or user_data.age > 120):
        raise HTTPException(status_code=400, detail="Age must be between 1 and 120")
    if user_data.gender and user_data.gender.lower() not in ["male", "female"]:
        raise HTTPException(status_code=400, detail="Gender must be either male or female")
    if user_data.name and (len(user_data.name) < 3 or len(user_data.name) > 100):
        raise HTTPException(status_code=400, detail="Name must be between 3 and 100 characters")
    if user_data.info and len(user_data.info) > 500:
        raise HTTPException(status_code=400, detail="Info must be less than 500 characters")
    # Update user fields
    db_user.name = user_data.name
    db_user.gender = user_data.gender
    db_user.age = user_data.age
    if user_data.info:
        db_user.info = user_data.info
    if user_data.telegram_id:
        db_user.telegram_id = user_data.telegram_id
    
    await db.commit()
    await db.refresh(db_user)
    logger.info(f"User updated successfully with ID: {db_user.id}")
    return db_user
