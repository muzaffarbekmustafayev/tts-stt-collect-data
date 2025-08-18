from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.core.logging import get_logger
from app.schemas.admin_users import AdminUserOut
from app.config import settings
from datetime import timedelta
from fastapi.security import OAuth2PasswordRequestForm
from app.services.admin_user_service import get_admin_user_by_username, verify_password, create_access_token, get_current_user

logger = get_logger("api.auth")
router = APIRouter(prefix="/auth", tags=["Auth"])

# Admin authentication endpoint (login)
@router.post("/")
async def auth_admin_user(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    try:
        user = await get_admin_user_by_username(form_data.username, db)
    except HTTPException:
        # User not found
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if user.is_active == False:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User is not active",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return {"access_token": access_token, "token_type": "bearer"}

# Get current user
@router.get("/me", response_model=AdminUserOut)
async def read_users_me(current_user: AdminUserOut = Depends(get_current_user)):
    return current_user