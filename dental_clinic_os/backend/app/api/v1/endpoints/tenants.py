"""
Tenants API endpoints (multi-tenant management)
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timedelta

from app.db.session import get_db
from app.core.security import get_current_admin, get_password_hash
from app.models.models import User, Tenant, TenantStatus, UserRole
from pydantic import BaseModel, Field, EmailStr

router = APIRouter(prefix="/tenants", tags=["tenants"])


# Schemas
class TenantCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=3, max_length=100, pattern="^[a-z0-9-]+$")
    domain: Optional[str] = None
    admin_email: EmailStr
    admin_password: str = Field(..., min_length=8)
    admin_first_name: str = Field(..., min_length=1, max_length=100)
    admin_last_name: str = Field(..., min_length=1, max_length=100)
    plan: str = "basic"
    trial_days: int = 30


class TenantUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[TenantStatus] = None
    plan: Optional[str] = None
    max_users: Optional[int] = None
    max_storage_gb: Optional[float] = None


class TenantResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    domain: Optional[str]
    status: TenantStatus
    plan: str
    max_users: int
    max_storage_gb: float
    monthly_revenue: float
    trial_ends_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True


@router.get("/", response_model=List[TenantResponse])
async def list_tenants(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    status: Optional[TenantStatus] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """List all tenants (super admin only)"""
    
    if current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin access required"
        )
    
    query = select(Tenant)
    
    if status:
        query = query.where(Tenant.status == status)
    
    query = query.order_by(Tenant.created_at.desc())
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    tenants = result.scalars().all()
    
    return tenants


@router.get("/{tenant_id}", response_model=TenantResponse)
async def get_tenant(
    tenant_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get tenant details"""
    tenant = await _get_tenant_by_id(tenant_id, db)
    
    # Only super admin can view any tenant
    if current_user.role != UserRole.SUPER_ADMIN:
        # Regular admins can only view their own tenant
        if tenant.id != current_user.tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this tenant"
            )
    
    return tenant


@router.post("/", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
async def create_tenant(
    tenant_data: TenantCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Create a new tenant with admin user"""
    
    if current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin access required"
        )
    
    # Check if slug already exists
    result = await db.execute(
        select(Tenant).where(Tenant.slug == tenant_data.slug)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant slug already exists"
        )
    
    # Create storage bucket and prefix
    storage_bucket = f"dental-clinic-{tenant_data.slug}"
    storage_prefix = f"{tenant_data.slug}/"
    
    # Create tenant
    tenant = Tenant(
        name=tenant_data.name,
        slug=tenant_data.slug,
        domain=tenant_data.domain,
        status=TenantStatus.TRIAL,
        plan=tenant_data.plan,
        storage_bucket=storage_bucket,
        storage_prefix=storage_prefix,
        trial_ends_at=datetime.utcnow() + timedelta(days=tenant_data.trial_days),
        settings={},
        feature_flags={}
    )
    
    db.add(tenant)
    await db.flush()  # Get tenant ID
    
    # Create admin user for tenant
    hashed_password = get_password_hash(tenant_data.admin_password)
    admin_user = User(
        tenant_id=tenant.id,
        email=tenant_data.admin_email,
        hashed_password=hashed_password,
        first_name=tenant_data.admin_first_name,
        last_name=tenant_data.admin_last_name,
        role=UserRole.ADMIN,
        is_active=True,
        is_verified=True
    )
    
    db.add(admin_user)
    await db.commit()
    await db.refresh(tenant)
    
    return tenant


@router.put("/{tenant_id}", response_model=TenantResponse)
async def update_tenant(
    tenant_id: UUID,
    tenant_data: TenantUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Update tenant details"""
    tenant = await _get_tenant_by_id(tenant_id, db)
    
    # Only super admin can modify any tenant
    if current_user.role != UserRole.SUPER_ADMIN:
        if tenant.id != current_user.tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to modify this tenant"
            )
        
        # Regular admins have limited permissions
        if tenant_data.status is not None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot modify tenant status"
            )
    
    # Update fields
    if tenant_data.name is not None:
        tenant.name = tenant_data.name
    if tenant_data.status is not None:
        tenant.status = tenant_data.status
    if tenant_data.plan is not None:
        tenant.plan = tenant_data.plan
    if tenant_data.max_users is not None:
        tenant.max_users = tenant_data.max_users
    if tenant_data.max_storage_gb is not None:
        tenant.max_storage_gb = tenant_data.max_storage_gb
    
    tenant.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(tenant)
    
    return tenant


@router.post("/{tenant_id}/suspend")
async def suspend_tenant(
    tenant_id: UUID,
    reason: str = "",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Suspend a tenant (super admin only)"""
    
    if current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin access required"
        )
    
    tenant = await _get_tenant_by_id(tenant_id, db)
    
    tenant.status = TenantStatus.SUSPENDED
    tenant.updated_at = datetime.utcnow()
    
    if reason:
        if "settings" not in tenant.settings or not isinstance(tenant.settings, dict):
            tenant.settings = {}
        tenant.settings["suspension_reason"] = reason
    
    await db.commit()
    
    return {"message": "Tenant suspended successfully"}


@router.post("/{tenant_id}/activate")
async def activate_tenant(
    tenant_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Activate a suspended tenant (super admin only)"""
    
    if current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin access required"
        )
    
    tenant = await _get_tenant_by_id(tenant_id, db)
    
    if tenant.status == TenantStatus.CANCELLED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot reactivate cancelled tenant"
        )
    
    tenant.status = TenantStatus.ACTIVE
    tenant.updated_at = datetime.utcnow()
    
    await db.commit()
    
    return {"message": "Tenant activated successfully"}


@router.get("/{tenant_id}/stats")
async def get_tenant_stats(
    tenant_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get tenant statistics"""
    tenant = await _get_tenant_by_id(tenant_id, db)
    
    # Only super admin or tenant admin can view stats
    if current_user.role != UserRole.SUPER_ADMIN and current_user.tenant_id != tenant.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this tenant's stats"
        )
    
    # Count users
    result = await db.execute(
        select(User).where(User.tenant_id == tenant.id)
    )
    users = result.scalars().all()
    
    user_count = len(users)
    active_user_count = sum(1 for u in users if u.is_active)
    
    # Count orders
    from app.models.models import Order
    result = await db.execute(
        select(Order).where(Order.tenant_id == tenant.id)
    )
    orders = result.scalars().all()
    
    order_count = len(orders)
    revenue = sum(o.total_amount for o in orders if o.status.value == "paid")
    
    return {
        "user_count": user_count,
        "active_user_count": active_user_count,
        "order_count": order_count,
        "monthly_revenue": tenant.monthly_revenue,
        "storage_used_gb": 0.0,  # Would be calculated from MinIO usage
        "storage_limit_gb": tenant.max_storage_gb
    }


async def _get_tenant_by_id(tenant_id: UUID, db: AsyncSession) -> Tenant:
    """Helper to get tenant by ID or raise 404"""
    result = await db.execute(
        select(Tenant).where(Tenant.id == tenant_id)
    )
    tenant = result.scalar_one_or_none()
    
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )
    
    return tenant
