"""
Users management API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from typing import List
from uuid import UUID
from datetime import datetime

from app.db.session import get_db
from app.core.security import (
    get_current_user, get_current_doctor, get_current_admin,
    require_tenant, get_password_hash, brute_force_protector
)
from app.models.models import User, UserRole
from app.schemas.schemas import UserCreate, UserUpdate, UserResponse, UserProfile

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserProfile)
async def get_my_profile(
    current_user: User = Depends(get_current_user)
):
    """Get current user's profile"""
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_my_profile(
    profile_data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update current user's profile"""
    
    # Update fields
    if profile_data.first_name is not None:
        current_user.first_name = profile_data.first_name
    if profile_data.last_name is not None:
        current_user.last_name = profile_data.last_name
    if profile_data.phone is not None:
        current_user.phone = profile_data.phone
    if profile_data.avatar_url is not None:
        current_user.avatar_url = profile_data.avatar_url
    
    current_user.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(current_user)
    
    return current_user


@router.get("/", response_model=List[UserResponse])
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    role: UserRole = None,
    search: str = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_doctor)
):
    """List users for the current tenant (doctor/admin only)"""
    tenant = require_tenant()
    
    # Build query
    query = select(User).where(User.tenant_id == tenant.id)
    
    # Filter by role if specified
    if role:
        query = query.where(User.role == role)
    
    # Search by name or email
    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            or_(
                User.first_name.ilike(search_pattern),
                User.last_name.ilike(search_pattern),
                User.email.ilike(search_pattern)
            )
        )
    
    # Order and paginate
    query = query.order_by(User.created_at.desc())
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    users = result.scalars().all()
    
    return users


@router.get("/{user_id}", response_model=UserProfile)
async def get_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_doctor)
):
    """Get a specific user (doctor/admin only)"""
    tenant = require_tenant()
    
    result = await db.execute(
        select(User).where(
            and_(
                User.id == user_id,
                User.tenant_id == tenant.id
            )
        )
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Patients can only see their own profile
    if current_user.role == UserRole.PATIENT and user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this user"
        )
    
    return user


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Create a new user (admin only)"""
    tenant = require_tenant()
    
    # Check if email already exists in tenant
    result = await db.execute(
        select(User).where(
            and_(
                User.tenant_id == tenant.id,
                User.email == user_data.email
            )
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered in this tenant"
        )
    
    # Validate role assignment
    if user_data.role == UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot create super admin users"
        )
    
    # Create user with hashed password
    hashed_password = get_password_hash(user_data.password)
    user = User(
        tenant_id=tenant.id,
        email=user_data.email,
        hashed_password=hashed_password,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        phone=user_data.phone,
        role=user_data.role,
        is_active=True,
        is_verified=True  # Admin-created users are auto-verified
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    return user


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    user_data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Update a user (admin only)"""
    tenant = require_tenant()
    
    result = await db.execute(
        select(User).where(
            and_(
                User.id == user_id,
                User.tenant_id == tenant.id
            )
        )
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Cannot modify super admin
    if user.role == UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot modify super admin users"
        )
    
    # Update fields
    if user_data.first_name is not None:
        user.first_name = user_data.first_name
    if user_data.last_name is not None:
        user.last_name = user_data.last_name
    if user_data.phone is not None:
        user.phone = user_data.phone
    if user_data.avatar_url is not None:
        user.avatar_url = user_data.avatar_url
    
    user.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(user)
    
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Delete/deactivate a user (admin only)"""
    tenant = require_tenant()
    
    result = await db.execute(
        select(User).where(
            and_(
                User.id == user_id,
                User.tenant_id == tenant.id
            )
        )
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Cannot delete super admin or yourself
    if user.role == UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot delete super admin users"
        )
    
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    # Soft delete (deactivate)
    user.is_active = False
    user.updated_at = datetime.utcnow()
    
    await db.commit()
    
    return None


@router.post("/{user_id}/activate")
async def activate_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Activate a user account (admin only)"""
    tenant = require_tenant()
    
    result = await db.execute(
        select(User).where(
            and_(
                User.id == user_id,
                User.tenant_id == tenant.id
            )
        )
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.is_active = True
    user.failed_login_attempts = 0
    user.locked_until = None
    user.updated_at = datetime.utcnow()
    
    await db.commit()
    
    return {"message": "User activated successfully"}


@router.post("/{user_id}/deactivate")
async def deactivate_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Deactivate a user account (admin only)"""
    tenant = require_tenant()
    
    result = await db.execute(
        select(User).where(
            and_(
                User.id == user_id,
                User.tenant_id == tenant.id
            )
        )
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own account"
        )
    
    user.is_active = False
    user.updated_at = datetime.utcnow()
    
    await db.commit()
    
    return {"message": "User deactivated successfully"}
