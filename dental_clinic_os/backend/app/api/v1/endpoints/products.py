"""
Products and Orders endpoints for e-commerce functionality
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from typing import List
from uuid import UUID
from datetime import datetime

from app.db.session import get_db
from app.core.security import get_current_user, get_current_admin
from app.api.deps import get_tenant_id, require_tenant_isolation
from app.models.models import User, Product, Order, OrderItem, UserRole
from app.schemas.schemas import (
    ProductCreate, ProductUpdate, ProductResponse,
    OrderCreate, OrderResponse, OrderItemCreate
)
import secrets

router = APIRouter(prefix="/products", tags=["products"])


# Products endpoints
@router.get("/", response_model=List[ProductResponse])
async def list_products(
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(require_tenant_isolation)
):
    """List all products for the current tenant"""
    result = await db.execute(
        select(Product)
        .where(Product.tenant_id == tenant_id)
        .where(Product.is_active == True)
        .order_by(Product.sort_order, Product.name)
    )
    products = result.scalars().all()
    return products


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: UUID,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(require_tenant_isolation)
):
    """Get a specific product"""
    result = await db.execute(
        select(Product).where(
            and_(
                Product.id == product_id,
                Product.tenant_id == tenant_id
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
    product = Product(
        name=product_data.name,
        description=product_data.description,
        price=product_data.price,
        features=product_data.features,
        tenant_id=current_user.tenant_id
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
    result = await db.execute(
        select(Product).where(
            and_(
                Product.id == product_id,
                Product.tenant_id == current_user.tenant_id
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
    
    product.updated_at = datetime.utcnow()
    
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
    result = await db.execute(
        select(Product).where(
            and_(
                Product.id == product_id,
                Product.tenant_id == current_user.tenant_id
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


# Orders endpoints
orders_router = APIRouter(prefix="/orders", tags=["orders"])


@orders_router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    order_data: OrderCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new order"""
    from app.models.models import OrderStatus
    
    # Calculate total
    total_amount = 0.0
    order_items_data = []
    
    for item in order_data.items:
        # Get product
        result = await db.execute(
            select(Product).where(
                and_(
                    Product.id == item.product_id,
                    Product.tenant_id == current_user.tenant_id,
                    Product.is_active == True
                )
            )
        )
        product = result.scalar_one_or_none()
        
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product {item.product_id} not found"
            )
        
        item_total = product.price * item.quantity
        total_amount += item_total
        
        order_items_data.append({
            "product": product,
            "quantity": item.quantity,
            "unit_price": product.price,
            "total_price": item_total
        })
    
    # Generate invoice number
    invoice_number = f"INV-{datetime.utcnow().strftime('%Y%m%d')}-{secrets.token_urlsafe(6).upper()}"
    
    # Create order
    order = Order(
        patient_id=current_user.id,
        tenant_id=current_user.tenant_id,
        total_amount=total_amount,
        status=OrderStatus.PENDING,
        invoice_number=invoice_number,
        idempotency_key=secrets.token_urlsafe(32)
    )
    
    db.add(order)
    await db.flush()  # Get order ID
    
    # Create order items
    for item_data in order_items_data:
        order_item = OrderItem(
            order_id=order.id,
            tenant_id=current_user.tenant_id,
            product_id=item_data["product"].id,
            quantity=item_data["quantity"],
            unit_price=item_data["unit_price"],
            total_price=item_data["total_price"]
        )
        db.add(order_item)
    
    await db.commit()
    await db.refresh(order)
    
    # Fetch complete order with items
    result = await db.execute(
        select(Order).where(Order.id == order.id)
    )
    return result.scalar_one()


@orders_router.get("/", response_model=List[OrderResponse])
async def list_orders(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List orders for current user"""
    result = await db.execute(
        select(Order).where(
            and_(
                Order.tenant_id == current_user.tenant_id,
                Order.patient_id == current_user.id
            )
        ).order_by(Order.created_at.desc())
    )
    orders = result.scalars().all()
    return orders


@orders_router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific order"""
    # Patients can only see their own orders, admins can see all
    from app.models.models import UserRole
    
    query = select(Order).where(
        and_(
            Order.id == order_id,
            Order.tenant_id == current_user.tenant_id
        )
    )
    
    if current_user.role != UserRole.ADMIN:
        query = query.where(Order.patient_id == current_user.id)
    
    result = await db.execute(query)
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    return order


@orders_router.get("/all/orders", response_model=List[OrderResponse])
async def list_all_orders(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """List all orders for tenant (admin only)"""
    result = await db.execute(
        select(Order)
        .where(Order.tenant_id == current_user.tenant_id)
        .order_by(Order.created_at.desc())
    )
    orders = result.scalars().all()
    return orders
