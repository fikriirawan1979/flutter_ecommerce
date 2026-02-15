"""
Products API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List
from uuid import UUID

from app.db.session import get_db
from app.core.security import get_current_user, get_current_admin, require_tenant
from app.models.models import User, Product, UserRole
from app.schemas.schemas import ProductCreate, ProductUpdate, ProductResponse

router = APIRouter(prefix="/products", tags=["products"])


@router.get("/", response_model=List[ProductResponse])
async def list_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    active_only: bool = True,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all products for the current tenant"""
    tenant = require_tenant()
    
    query = select(Product).where(Product.tenant_id == tenant.id)
    
    if active_only:
        query = query.where(Product.is_active == True)
    
    query = query.order_by(Product.sort_order, Product.created_at)
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    products = result.scalars().all()
    
    return products


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific product"""
    tenant = require_tenant()
    
    result = await db.execute(
        select(Product).where(
            and_(
                Product.id == product_id,
                Product.tenant_id == tenant.id
            )
        )
    )
    product = result.scalar_one_or_none()
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    return product


@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    product_data: ProductCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Create a new product (admin only)"""
    tenant = require_tenant()
    
    product = Product(
        tenant_id=tenant.id,
        name=product_data.name,
        description=product_data.description,
        price=product_data.price,
        features=product_data.features,
        is_active=True,
        sort_order=0
    )
    
    db.add(product)
    await db.commit()
    await db.refresh(product)
    
    return product


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: UUID,
    product_data: ProductUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Update a product (admin only)"""
    tenant = require_tenant()
    
    result = await db.execute(
        select(Product).where(
            and_(
                Product.id == product_id,
                Product.tenant_id == tenant.id
            )
        )
    )
    product = result.scalar_one_or_none()
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Update fields
    if product_data.name is not None:
        product.name = product_data.name
    if product_data.description is not None:
        product.description = product_data.description
    if product_data.price is not None:
        product.price = product_data.price
    if product_data.features is not None:
        product.features = product_data.features
    if product_data.is_active is not None:
        product.is_active = product_data.is_active
    
    await db.commit()
    await db.refresh(product)
    
    return product


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Delete a product (admin only)"""
    tenant = require_tenant()
    
    result = await db.execute(
        select(Product).where(
            and_(
                Product.id == product_id,
                Product.tenant_id == tenant.id
            )
        )
    )
    product = result.scalar_one_or_none()
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    await db.delete(product)
    await db.commit()
    
    return None
