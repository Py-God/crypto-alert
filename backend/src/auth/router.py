# src/auth/router.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.auth import schemas, service
from src.auth.dependencies import get_current_user
from src.auth.models import User

router = APIRouter()


@router.post("/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: schemas.UserRegister,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new user.
    
    - **email**: Valid email address
    - **username**: 3-50 characters, letters/numbers/underscores only
    - **password**: Minimum 8 characters, must contain uppercase, lowercase, and number
    - **phone_number**: Optional phone number
    """
    # Check if email already exists
    existing_user = await service.get_user_by_email(db, user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Check if username already exists
    existing_user = await service.get_user_by_username(db, user_data.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    
    # Create user
    user = await service.create_user(db, user_data)
    return user


@router.post("/login", response_model=schemas.TokenResponse)
async def login(
    credentials: schemas.UserLogin,
    db: AsyncSession = Depends(get_db)
):
    """
    Login with email and password.
    
    Returns access token (30 min) and refresh token (7 days).
    """
    # Authenticate user
    user = await service.authenticate_user(db, credentials.email, credentials.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )
    
    # Generate tokens
    access_token = service.create_access_token(data={"sub": str(user.id)})
    refresh_token = service.create_refresh_token(data={"sub": str(user.id)})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post("/refresh", response_model=schemas.TokenResponse)
async def refresh_token(
    token_data: schemas.TokenRefresh,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a new access token using refresh token.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid refresh token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Decode refresh token
    payload = service.decode_token(token_data.refresh_token)
    if payload is None:
        raise credentials_exception
    
    user_id: str = payload.get("sub")
    token_type: str = payload.get("type")
    
    if user_id is None or token_type != "refresh":
        raise credentials_exception
    
    # Verify user exists
    user = await service.get_user_by_id(db, int(user_id))
    if user is None or not user.is_active:
        raise credentials_exception
    
    # Create new access token
    new_access_token = service.create_access_token(data={"sub": user_id})
    
    return {
        "access_token": new_access_token,
        "refresh_token": token_data.refresh_token,
        "token_type": "bearer"
    }


@router.get("/me", response_model=schemas.UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get current authenticated user's information.
    
    Requires: Bearer token in Authorization header
    """
    return current_user


@router.post("/logout", response_model=schemas.MessageResponse)
async def logout(
    current_user: User = Depends(get_current_user)
):
    """
    Logout current user.
    
    Note: Since we're using stateless JWT, this is mainly for client-side cleanup.
    In production, you'd want to blacklist the token in Redis.
    """
    return {"message": "Successfully logged out"}