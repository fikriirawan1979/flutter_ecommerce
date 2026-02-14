from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import timedelta
from typing import Optional
from uuid import UUID

from app.db.session import get_db
from app.core.security import (
    verify_password, get_password_hash, create_access_token,
    create_refresh_token, decode_token,
    brute_force_protector, rate_limiter
)
from app.api.deps import get_current_user
from app.core.config import settings
from app.models.models import User, UserRole, Tenant
from app.schemas.schemas import (
    UserCreate, UserResponse, LoginRequest, Token, RefreshRequest
)

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/register", response_model=Token)
async def register(
    user_data: UserCreate,
    tenant_id: Optional[str] = Header(None, alias="X-Tenant-ID"),
    db: AsyncSession = Depends(get_db)
):
    """Register a new user with tenant isolation"""
    # Rate limiting
    client_ip = "register_endpoint"  # In production, get from request
    if not rate_limiter.is_allowed(client_ip, max_requests=10, window_seconds=60):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many registration attempts"
        )
    
    # Validate tenant if provided
    if tenant_id:
        tenant_result = await db.execute(
            select(Tenant).where(Tenant.id == UUID(tenant_id))
        )
        if not tenant_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid tenant"
            )
    else:
        # Use default tenant or require one based on settings
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Tenant-ID header is required"
        )
    
    # Check if email exists within tenant
    result = await db.execute(
        select(User).where(
            User.email == user_data.email,
            User.tenant_id == UUID(tenant_id)
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered in this tenant"
        )
    
    # Create user with tenant
    hashed_password = get_password_hash(user_data.password)
    user = User(
        email=user_data.email,
        hashed_password=hashed_password,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        phone=user_data.phone,
        role=user_data.role,
        tenant_id=UUID(tenant_id)
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    # Generate tokens with tenant context
    token_data = {"sub": str(user.id), "role": user.role.value}
    access_token = create_access_token(token_data, tenant_id=tenant_id)
    refresh_token = create_refresh_token(token_data, tenant_id=tenant_id)
    
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
    """Login user with brute force protection"""
    # Check brute force protection
    is_allowed, error_message = brute_force_protector.record_attempt(
        credentials.email, 
        success=False  # Will update on success
    )
    
    if not is_allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=error_message
        )
    
    # Find user (across all tenants - email identifies user)
    result = await db.execute(
        select(User).where(User.email == credentials.email)
    )
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(credentials.password, user.hashed_password):
        remaining = 5 - brute_force_protector._attempts.get(credentials.email, {}).get("count", 0)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid email or password. {remaining} attempts remaining."
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated"
        )
    
    # Record successful login
    brute_force_protector.record_attempt(credentials.email, success=True)
    
    # Update last login
    from datetime import datetime
    user.last_login = datetime.utcnow()
    await db.commit()
    
    # Generate tokens with tenant context
    tenant_id = str(user.tenant_id)
    token_data = {"sub": str(user.id), "role": user.role.value}
    access_token = create_access_token(token_data, tenant_id=tenant_id)
    refresh_token = create_refresh_token(token_data, tenant_id=tenant_id)
    
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
    """Refresh access token with tenant context preservation"""
    payload = decode_token(refresh_data.refresh_token)
    
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    user_id = payload.get("sub")
    role = payload.get("role")
    tenant_id = payload.get("tenant_id")
    
    token_data = {"sub": user_id, "role": role}
    access_token = create_access_token(token_data, tenant_id=tenant_id)
    new_refresh_token = create_refresh_token(token_data, tenant_id=tenant_id)
    
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
async def seed_demo_users(
    tenant_id: Optional[str] = Header(None, alias="X-Tenant-ID"),
    db: AsyncSession = Depends(get_db)
):
    """Seed demo users for testing (development only)"""
    from app.core.config import settings
    
    if settings.is_production:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Demo user seeding is not allowed in production"
        )
    
    # Validate tenant
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Tenant-ID header is required"
        )
    
    tenant_result = await db.execute(
        select(Tenant).where(Tenant.id == UUID(tenant_id))
    )
    if not tenant_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid tenant"
        )
    
    demo_users = [
        {
            "email": f"patient-{tenant_id[:8]}@demo.com",
            "password": "Password123!",
            "first_name": "Demo",
            "last_name": "Patient",
            "role": UserRole.PATIENT
        },
        {
            "email": f"doctor-{tenant_id[:8]}@demo.com",
            "password": "Password123!",
            "first_name": "Demo",
            "last_name": "Doctor",
            "role": UserRole.DOCTOR
        },
        {
            "email": f"admin-{tenant_id[:8]}@demo.com",
            "password": "Password123!",
            "first_name": "Demo",
            "last_name": "Admin",
            "role": UserRole.ADMIN
        }
    ]
    
    created = []
    for user_data in demo_users:
        result = await db.execute(
            select(User).where(
                User.email == user_data["email"],
                User.tenant_id == UUID(tenant_id)
            )
        )
        if not result.scalar_one_or_none():
            user = User(
                email=user_data["email"],
                hashed_password=get_password_hash(user_data["password"]),
                first_name=user_data["first_name"],
                last_name=user_data["last_name"],
                role=user_data["role"],
                tenant_id=UUID(tenant_id)
            )
            db.add(user)
            created.append(user_data["email"])
    
    await db.commit()
    
    return {
        "message": "Demo users created",
        "users": created,
        "tenant_id": tenant_id,
        "credentials": "Use the emails listed above with password: Password123!"
    }