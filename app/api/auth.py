from fastapi import APIRouter, Depends, HTTPException, status, Response, Request, Body
from app.core.logging import get_logger
from app.schemas.admin_users import AdminUserOut
from app.config import settings
from datetime import timedelta
from jose import JWTError
from fastapi.security import OAuth2PasswordRequestForm
from app.services.admin_user_service import get_admin_user_by_username, verify_password, create_access_token, get_current_user, get_payload
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Union

logger = get_logger("api.auth")
router = APIRouter(prefix="/auth", tags=["Auth"])

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    token: str
    role: str

# Admin authentication endpoint (login) - Flexible format
@router.post("/login", response_model=LoginResponse)
async def auth_admin_user(request: Request):
    """
    Login endpoint that accepts both JSON and form data
    """
    content_type = request.headers.get("content-type", "")
    
    try:
        # Try to parse as JSON first
        if "application/json" in content_type:
            body = await request.json()
            username = body.get("username")
            password = body.get("password")
        else:
            # Try form data
            form = await request.form()
            username = form.get("username")
            password = form.get("password")
        
        if not username or not password:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Username and password are required"
            )
        
        logger.info(f"Login attempt for user: {username}")
        
        # Get user
        try:
            user = await get_admin_user_by_username(username)
        except HTTPException:
            logger.warning(f"User not found: {username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Check if active
        if not user.is_active:
            logger.warning(f"Inactive user login attempt: {username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User is not active",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Verify password
        if not verify_password(password, user.password):
            logger.warning(f"Invalid password for user: {username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Create token
        token = create_access_token(
            data={"sub": user.username, "role": user.role},
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        )
        
        logger.info(f"Login successful for user: {username}")
        
        return {
            "token": token,
            "role": user.role
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

# Get current user
@router.get("/me", response_model=AdminUserOut)
async def read_users_me(current_user: dict = Depends(get_current_user)):
    user = await get_admin_user_by_username(current_user["username"])
    return {
        "id": str(user.id),
        "username": user.username,
        "role": user.role,
        "is_active": user.is_active,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "updated_at": user.updated_at.isoformat() if user.updated_at else None
    }