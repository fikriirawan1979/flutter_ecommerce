"""
Orders and Products API Endpoints
Multi-tenant e-commerce functionality with Stripe integration
"""

from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from app.db.session import get_db
from app.api.deps import get_current_active_user, get_current_user
from app.core.security import rate_limiter
from app.models.models import (
    User, Order, OrderItem, Product, OrderStatus, Assessment,
    AssessmentStatus, UserRole
)
from app.schemas.schemas import (
    OrderCreate, OrderResponse, ProductResponse, OrderItemCreate
)
from app.services.stripe_service import stripe_service

router = APIRouter(prefix="/orders", tags=["orders"])


@router.get("/products", response_model=List[ProductResponse])
async def list_products(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """List all active products for current tenant"""
    result = await db.execute(
        select(Product).where(
            and_(
                Product.tenant_id == current_user.tenant_id,
                Product.is_active == True
            )
        ).order_by(Product.sort_order)
    )
    products = result.scalars().all()
    return products


@router.post("/create", response_model=OrderResponse)
async def create_order(
    order_data: OrderCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new order"""
    # Validate all products exist and belong to tenant
    total_amount = 0.0
    order_items = []
    
    for item in order_data.items:
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
        
        order_items.append({
            "product": product,
            "quantity": item.quantity,
            "unit_price": product.price,
            "total_price": item_total
        })
    
    # Generate invoice number
    invoice_number = f"INV-{datetime.utcnow().strftime('%Y%m%d')}-{current_user.id.hex[:8].upper()}"
    
    # Create order
    order = Order(
        patient_id=current_user.id,
        tenant_id=current_user.tenant_id,
        total_amount=total_amount,
        status=OrderStatus.PENDING,
        invoice_number=invoice_number
    )
    
    db.add(order)
    await db.flush()  # Get order ID
    
    # Create order items
    for item_data in order_items:
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
    
    return order


@router.get("/my-orders", response_model=List[OrderResponse])
async def get_my_orders(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get current user's orders"""
    result = await db.execute(
        select(Order).where(
            and_(
                Order.patient_id == current_user.id,
                Order.tenant_id == current_user.tenant_id
            )
        ).order_by(Order.created_at.desc())
    )
    orders = result.scalars().all()
    return orders


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get order details with tenant isolation"""
    result = await db.execute(
        select(Order).where(
            and_(
                Order.id == order_id,
                Order.tenant_id == current_user.tenant_id
            )
        )
    )
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    # Verify user has access (patient who ordered, doctor, or admin)
    if (order.patient_id != current_user.id and 
        current_user.role not in [UserRole.DOCTOR, UserRole.ADMIN]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    return order


@router.post("/{order_id}/pay")
async def create_payment_intent(
    order_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create Stripe PaymentIntent for order"""
    # Get order with tenant isolation
    result = await db.execute(
        select(Order).where(
            and_(
                Order.id == order_id,
                Order.tenant_id == current_user.tenant_id,
                Order.patient_id == current_user.id
            )
        )
    )
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    if order.status != OrderStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Order cannot be paid. Current status: {order.status}"
        )
    
    # Create PaymentIntent via Stripe
    try:
        payment_data = await stripe_service.create_payment_intent(
            db=db,
            order_id=order.id,
            tenant_id=current_user.tenant_id,
            user_id=current_user.id,
            amount=order.total_amount
        )
        
        return {
            "client_secret": payment_data["client_secret"],
            "payment_intent_id": payment_data["payment_intent_id"],
            "amount": payment_data["amount"]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Payment processing error: {str(e)}"
        )


@router.post("/{order_id}/cancel")
async def cancel_order(
    order_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Cancel a pending order"""
    result = await db.execute(
        select(Order).where(
            and_(
                Order.id == order_id,
                Order.tenant_id == current_user.tenant_id,
                Order.patient_id == current_user.id
            )
        )
    )
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    if order.status != OrderStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only pending orders can be cancelled"
        )
    
    order.status = OrderStatus.CANCELLED
    await db.commit()
    
    return {"message": "Order cancelled successfully"}


@router.get("/admin/all", response_model=List[OrderResponse])
async def get_all_orders(
    status: Optional[OrderStatus] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all orders for tenant (admin/doctor only)"""
    if current_user.role not in [UserRole.DOCTOR, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    query = select(Order).where(Order.tenant_id == current_user.tenant_id)
    
    if status:
        query = query.where(Order.status == status)
    
    result = await db.execute(query.order_by(Order.created_at.desc()))
    orders = result.scalars().all()
    return orders
