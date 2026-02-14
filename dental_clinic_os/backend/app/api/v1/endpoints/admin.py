"""
Admin endpoints for user management, tenant configuration, and system settings
Role-based access control enforced
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from app.db.session import get_db
from app.api.deps import get_current_admin, get_current_active_user
from app.models.models import User, UserRole, Tenant, Order, Assessment, AuditLog
from app.schemas.schemas import UserResponse, UserUpdate

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users", response_model=List[UserResponse])
async def list_users(
    role: Optional[UserRole] = None,
    is_active: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """List all users in tenant (admin only)"""
    query = select(User).where(User.tenant_id == current_user.tenant_id)
    
    if role:
        query = query.where(User.role == role)
    if is_active is not None:
        query = query.where(User.is_active == is_active)
    
    result = await db.execute(query.order_by(User.created_at.desc()))
    users = result.scalars().all()
    return users


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get user details (admin only)"""
    result = await db.execute(
        select(User).where(
            and_(
                User.id == user_id,
                User.tenant_id == current_user.tenant_id
            )
        )
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user


@router.patch("/users/{user_id}")
async def update_user(
    user_id: UUID,
    user_data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Update user (admin only)"""
    result = await db.execute(
        select(User).where(
            and_(
                User.id == user_id,
                User.tenant_id == current_user.tenant_id
            )
        )
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update fields
    if user_data.first_name:
        user.first_name = user_data.first_name
    if user_data.last_name:
        user.last_name = user_data.last_name
    if user_data.phone:
        user.phone = user_data.phone
    if user_data.avatar_url:
        user.avatar_url = user_data.avatar_url
    
    await db.commit()
    await db.refresh(user)
    
    return user


@router.post("/users/{user_id}/deactivate")
async def deactivate_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Deactivate a user (admin only)"""
    # Prevent self-deactivation
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate yourself"
        )
    
    result = await db.execute(
        select(User).where(
            and_(
                User.id == user_id,
                User.tenant_id == current_user.tenant_id
            )
        )
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.is_active = False
    await db.commit()
    
    return {"message": "User deactivated successfully"}


@router.post("/users/{user_id}/activate")
async def activate_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Activate a user (admin only)"""
    result = await db.execute(
        select(User).where(
            and_(
                User.id == user_id,
                User.tenant_id == current_user.tenant_id
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
    await db.commit()
    
    return {"message": "User activated successfully"}


@router.get("/dashboard-stats")
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get dashboard statistics for tenant"""
    # Only doctors and admins can see full stats
    if current_user.role not in [UserRole.DOCTOR, UserRole.ADMIN]:
        # Return limited stats for patients
        result = await db.execute(
            select(func.count()).where(
                and_(
                    Assessment.patient_id == current_user.id,
                    Assessment.tenant_id == current_user.tenant_id
                )
            )
        )
        total_assessments = result.scalar()
        
        return {
            "total_assessments": total_assessments,
            "role": current_user.role.value
        }
    
    # Full stats for doctors and admins
    # Total orders
    result = await db.execute(
        select(func.count(), func.sum(Order.total_amount)).where(
            Order.tenant_id == current_user.tenant_id
        )
    )
    total_orders, total_revenue = result.first()
    
    # Total assessments
    result = await db.execute(
        select(func.count()).where(
            Assessment.tenant_id == current_user.tenant_id
        )
    )
    total_assessments = result.scalar()
    
    # Pending assessments
    result = await db.execute(
        select(func.count()).where(
            and_(
                Assessment.tenant_id == current_user.tenant_id,
                Assessment.status.in_(["uploaded", "in_review"])
            )
        )
    )
    pending_reviews = result.scalar()
    
    # Total users
    result = await db.execute(
        select(func.count()).where(
            User.tenant_id == current_user.tenant_id
        )
    )
    total_users = result.scalar()
    
    # This month's revenue
    from datetime import timedelta
    last_month = datetime.utcnow() - timedelta(days=30)
    result = await db.execute(
        select(func.sum(Order.total_amount)).where(
            and_(
                Order.tenant_id == current_user.tenant_id,
                Order.paid_at >= last_month
            )
        )
    )
    monthly_revenue = result.scalar() or 0
    
    return {
        "total_revenue": float(total_revenue or 0),
        "total_orders": total_orders,
        "total_assessments": total_assessments,
        "pending_reviews": pending_reviews,
        "total_users": total_users,
        "monthly_revenue": float(monthly_revenue),
        "role": current_user.role.value
    }


@router.get("/audit-logs")
async def get_audit_logs(
    limit: int = 100,
    action: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get audit logs (admin only)"""
    query = select(AuditLog).where(
        AuditLog.tenant_id == current_user.tenant_id
    )
    
    if action:
        query = query.where(AuditLog.action == action)
    
    result = await db.execute(
        query.order_by(AuditLog.created_at.desc()).limit(limit)
    )
    logs = result.scalars().all()
    
    return [
        {
            "id": str(log.id),
            "action": log.action,
            "resource_type": log.resource_type,
            "resource_id": str(log.resource_id) if log.resource_id else None,
            "user_id": str(log.user_id) if log.user_id else None,
            "ip_address": log.ip_address,
            "success": log.success,
            "created_at": log.created_at
        }
        for log in logs
    ]


@router.get("/tenant/settings")
async def get_tenant_settings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get tenant settings"""
    result = await db.execute(
        select(Tenant).where(Tenant.id == current_user.tenant_id)
    )
    tenant = result.scalar_one()
    
    return {
        "id": str(tenant.id),
        "name": tenant.name,
        "slug": tenant.slug,
        "status": tenant.status.value,
        "plan": tenant.plan,
        "max_users": tenant.max_users,
        "max_storage_gb": tenant.max_storage_gb,
        "settings": tenant.settings,
        "feature_flags": tenant.feature_flags
    }


@router.patch("/tenant/settings")
async def update_tenant_settings(
    settings_update: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Update tenant settings (admin only)"""
    result = await db.execute(
        select(Tenant).where(Tenant.id == current_user.tenant_id)
    )
    tenant = result.scalar_one()
    
    # Update allowed fields
    if "settings" in settings_update:
        tenant.settings.update(settings_update["settings"])
    if "feature_flags" in settings_update:
        tenant.feature_flags.update(settings_update["feature_flags"])
    
    await db.commit()
    
    return {
        "message": "Settings updated",
        "settings": tenant.settings,
        "feature_flags": tenant.feature_flags
    }
