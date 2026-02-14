from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import timedelta
import uuid

from app.db.session import get_db
from app.core.security import (
    verify_password, get_password_hash, create_access_token,
    create_refresh_token, decode_token, get_current_user,
    brute_force_protector
)
from app.core.config import settings
from app.models.models import User, UserRole, Tenant, TenantStatus
from app.schemas.schemas import (
    UserCreate, UserResponse, LoginRequest, Token, RefreshRequest
)

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/register", response_model=Token)
async def register(
    user_data: UserCreate,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Register a new user with tenant context"""
    # For registration without tenant, create/get a default tenant
    # In production, this should be handled through an invitation system
    
    # Check if email exists globally (across all tenants for security)
    result = await db.execute(
        select(User).where(User.email == user_data.email)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create or get default tenant
    # For demo purposes, we'll create a personal tenant
    tenant_slug = f"{user_data.email.split('@')[0]}-{uuid.uuid4().hex[:8]}"
    tenant = Tenant(
        name=f"{user_data.first_name} {user_data.last_name}'s Clinic",
        slug=tenant_slug,
        status=TenantStatus.TRIAL,
        storage_bucket=f"dental-{tenant_slug}",
        storage_prefix=tenant_slug[:20],
        plan="trial",
        max_users=5,
        max_storage_gb=10.0
    )
    db.add(tenant)
    await db.flush()  # Get tenant ID
    
    # Create user with tenant context
    hashed_password = get_password_hash(user_data.password)
    user = User(
        email=user_data.email,
        hashed_password=hashed_password,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        phone=user_data.phone,
        role=user_data.role,
        tenant_id=tenant.id
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    await db.refresh(tenant)
    
    # Generate tokens with tenant context
    token_data = {
        "sub": str(user.id),
        "role": user.role.value,
        "tenant_id": str(tenant.id)
    }
    access_token = create_access_token(
        data=token_data,
        tenant_id=str(tenant.id)
    )
    refresh_token = create_refresh_token(
        data=token_data,
        tenant_id=str(tenant.id)
    )
    
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
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Login user with brute force protection"""
    client_ip = request.client.host if request.client else "unknown"
    identifier = f"{client_ip}:{credentials.email}"
    
    # Check if account is locked
    if brute_force_protector.is_locked(identifier):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Account temporarily locked due to too many failed attempts"
        )
    
    # Find user
    result = await db.execute(
        select(User).where(User.email == credentials.email)
    )
    user = result.scalar_one_or_none()
    
    # Verify credentials
    password_valid = False
    if user:
        password_valid = verify_password(credentials.password, user.hashed_password)
    
    if not user or not password_valid:
        # Record failed attempt
        is_allowed, error_msg = brute_force_protector.record_attempt(
            identifier, success=False
        )
        if not is_allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=error_msg
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated"
        )
    
    # Check tenant status
    tenant_result = await db.execute(
        select(Tenant).where(Tenant.id == user.tenant_id)
    )
    tenant = tenant_result.scalar_one_or_none()
    
    if not tenant or tenant.status != TenantStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant account is not active"
        )
    
    # Record successful login and reset attempts
    brute_force_protector.record_attempt(identifier, success=True)
    
    # Update last login
    from datetime import datetime
    user.last_login = datetime.utcnow()
    await db.commit()
    
    # Generate tokens with tenant context
    token_data = {
        "sub": str(user.id),
        "role": user.role.value,
        "tenant_id": str(tenant.id)
    }
    access_token = create_access_token(
        data=token_data,
        tenant_id=str(tenant.id)
    )
    refresh_token = create_refresh_token(
        data=token_data,
        tenant_id=str(tenant.id)
    )
    
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
    """Refresh access token with tenant context"""
    payload = decode_token(refresh_data.refresh_token)
    
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    user_id = payload.get("sub")
    role = payload.get("role")
    tenant_id = payload.get("tenant_id")
    
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: missing tenant context"
        )
    
    token_data = {
        "sub": user_id,
        "role": role,
        "tenant_id": tenant_id
    }
    access_token = create_access_token(
        data=token_data,
        tenant_id=tenant_id
    )
    new_refresh_token = create_refresh_token(
        data=token_data,
        tenant_id=tenant_id
    )
    
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
    # Create a demo tenant
    demo_tenant = Tenant(
        name="Demo Dental Clinic",
        slug="demo-clinic",
        status=TenantStatus.ACTIVE,
        storage_bucket="dental-demo-clinic",
        storage_prefix="demo",
        plan="professional",
        max_users=50,
        max_storage_gb=100.0
    )
    db.add(demo_tenant)
    await db.flush()  # Get tenant ID
    
    demo_users = [
        {
            "email": "patient@demo.com",
            "password": "Password123!",  # Stronger password
            "first_name": "Demo",
            "last_name": "Patient",
            "role": UserRole.PATIENT
        },
        {
            "email": "doctor@demo.com",
            "password": "Password123!",
            "first_name": "Demo",
            "last_name": "Doctor",
            "role": UserRole.DOCTOR
        },
        {
            "email": "admin@demo.com",
            "password": "Password123!",
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
                role=user_data["role"],
                tenant_id=demo_tenant.id
            )
            db.add(user)
            created.append(user_data["email"])
    
    await db.commit()
    
    return {
        "message": "Demo users created",
        "users": created,
        "credentials": "Email: [role]@demo.com, Password: Password123!",
        "tenant_id": str(demo_tenant.id)
    }