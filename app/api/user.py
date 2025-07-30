from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserOut
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from app.core.logging import get_logger

logger = get_logger("api.user")
router = APIRouter(prefix="/users", tags=["Users"])

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

@router.get("/{telegram_id}", response_model=UserOut)
async def get_user_by_telegram_id(telegram_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()
    if not user:
        logger.warning(f"User not found with telegram_id: {telegram_id}")
        raise HTTPException(status_code=404, detail="User not found")
    logger.info(f"User found with ID: {user.id}")
    return user
  
@router.get("/by-id/{id}", response_model=UserOut)
async def get_user_by_id(id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == id))
    user = result.scalar_one_or_none()
    if not user:
        logger.warning(f"User not found with ID: {id}")
        raise HTTPException(status_code=404, detail="User not found")
    logger.info(f"User found with telegram_id: {user.telegram_id}")
    return user
  
@router.get("/", response_model=list[UserOut])
async def get_all_users(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User))
    users = result.scalars().all()
    logger.info(f"Found {len(users)} users")
    return users
  
@router.put("/{id}", response_model=UserOut)
async def update_user(id: int, user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == id))
    db_user = result.scalar_one_or_none()
    if not db_user:
        logger.warning(f"User not found with ID: {id}")
        raise HTTPException(status_code=404, detail="User not found")
    
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
