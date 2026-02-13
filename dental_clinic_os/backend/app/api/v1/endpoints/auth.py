from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import timedelta

from app.db.session import get_db
from app.core.security import (
    verify_password, get_password_hash, create_access_token,
    create_refresh_token, decode_token, get_current_user
)
from app.core.config import settings
from app.models.models import User, UserRole
from app.schemas.schemas import (
    UserCreate, UserResponse, LoginRequest, Token, RefreshRequest
)

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/register", response_model=Token)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """Register a new user"""
    # Check if email exists
    result = await db.execute(
        select(User).where(User.email == user_data.email)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user
    hashed_password = get_password_hash(user_data.password)
    user = User(
        email=user_data.email,
        hashed_password=hashed_password,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        phone=user_data.phone,
        role=user_data.role
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    # Generate tokens
    token_data = {"sub": str(user.id), "role": user.role.value}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    
    from datetime import datetime
    expires_at = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_at=expires_at
    )

@router.post("/login", response_model=Token)
async def login(
    credentials: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """Login user"""
    # Find user
    result = await db.execute(
        select(User).where(User.email == credentials.email)
    )
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated"
        )
    
    # Update last login
    from datetime import datetime
    user.last_login = datetime.utcnow()
    await db.commit()
    
    # Generate tokens
    token_data = {"sub": str(user.id), "role": user.role.value}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    
    expires_at = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_at=expires_at
    )

@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_data: RefreshRequest
):
    """Refresh access token"""
    payload = decode_token(refresh_data.refresh_token)
    
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    user_id = payload.get("sub")
    role = payload.get("role")
    
    token_data = {"sub": user_id, "role": role}
    access_token = create_access_token(token_data)
    new_refresh_token = create_refresh_token(token_data)
    
    from datetime import datetime
    expires_at = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    return Token(
        access_token=access_token,
        refresh_token=new_refresh_token,
        expires_at=expires_at
    )

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Get current user information"""
    return current_user

@router.post("/seed-demo-users")
async def seed_demo_users(db: AsyncSession = Depends(get_db)):
    """Seed demo users for testing (development only)"""
    demo_users = [
        {
            "email": "patient@demo.com",
            "password": "password123",
            "first_name": "Demo",
            "last_name": "Patient",
            "role": UserRole.PATIENT
        },
        {
            "email": "doctor@demo.com",
            "password": "password123",
            "first_name": "Demo",
            "last_name": "Doctor",
            "role": UserRole.DOCTOR
        },
        {
            "email": "admin@demo.com",
            "password": "password123",
            "first_name": "Demo",
            "last_name": "Admin",
            "role": UserRole.ADMIN
        }
    ]
    
    created = []
    for user_data in demo_users:
        result = await db.execute(
            select(User).where(User.email == user_data["email"])
        )
        if not result.scalar_one_or_none():
            user = User(
                email=user_data["email"],
                hashed_password=get_password_hash(user_data["password"]),
                first_name=user_data["first_name"],
                last_name=user_data["last_name"],
                role=user_data["role"]
            )
            db.add(user)
            created.append(user_data["email"])
    
    await db.commit()
    
    return {
        "message": "Demo users created",
        "users": created,
        "credentials": "Email: [role]@demo.com, Password: password123"
    }