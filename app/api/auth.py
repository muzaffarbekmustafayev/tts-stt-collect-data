from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.core.logging import get_logger
from app.schemas.admin_users import AdminUserOut
from app.config import settings
from datetime import timedelta
from jose import JWTError
from fastapi.security import OAuth2PasswordRequestForm
from app.services.admin_user_service import get_admin_user_by_username, verify_password, create_access_token, get_current_user, get_payload
from fastapi.responses import JSONResponse

logger = get_logger("api.auth")
router = APIRouter(prefix="/auth", tags=["Auth"])

# Admin authentication endpoint (login)
@router.post("/login")
async def auth_admin_user(response: Response, form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
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
    
    token = create_access_token(
        data={"sub": user.username, "role": user.role},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    
    content = {
        "token": token
    }
    return JSONResponse(content=content, status_code=status.HTTP_200_OK)
    

# Get current user
@router.get("/me", response_model=AdminUserOut)
async def read_users_me(current_user: AdminUserOut = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    user = await get_admin_user_by_username(current_user["username"], db)
    content = {
        "id": user.id,
        "username": user.username,
        "role": user.role,
        "is_active": user.is_active,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }
    return JSONResponse(content=content, status_code=status.HTTP_200_OK)