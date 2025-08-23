from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
from app.models.admin_users import AdminUser
from app.schemas.admin_users import AdminUserCreate
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta, UTC
from app.config import settings
from app.db.session import get_db


# Config
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", scheme_name="Bearer")



async def get_admin_user_by_id(id: int, db: AsyncSession) -> AdminUser | None:
    result = await db.execute(select(AdminUser).where(AdminUser.id == id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

async def get_admin_user_by_username(username: str, db: AsyncSession) -> AdminUser | None:
    result = await db.execute(select(AdminUser).where(AdminUser.username == username))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

async def create_admin_user(user: AdminUserCreate, db: AsyncSession) -> AdminUser:
    new_user = AdminUser(**user.model_dump())
    if len(new_user.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters long")
    new_user.password = hash_password(new_user.password)
    db.add(new_user)
    try:
        await db.commit()
        await db.refresh(new_user)
        return new_user
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="User already exists")

async def update_admin_user(id: int, user_data: AdminUserCreate, db: AsyncSession) -> AdminUser:
    user = await get_admin_user_by_id(id, db)
    if len(user_data.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters long")
    user.username = user_data.username
    user.password = hash_password(user_data.password)
    user.role = user_data.role
    user.is_active = user_data.is_active
    await db.commit()
    await db.refresh(user)
    return user


async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
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
    
    user = await get_admin_user_by_username(username, db)
    return {"username": user.username, "role": user.role}


def get_current_admin_user (current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if current_user["role"] != "admin" and current_user["role"] != "superadmin" and current_user["is_active"] == False:
        raise HTTPException(status_code=403, detail="You don't have permission to access this resource")
    return current_user

def get_current_superadmin_user (current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if current_user["role"] != "superadmin":
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
