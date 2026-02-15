"""
Orders API endpoints with Stripe integration
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List
from uuid import UUID
from datetime import datetime, timedelta
import stripe

from app.db.session import get_db
from app.core.security import get_current_user, get_current_doctor, get_current_admin, require_tenant, generate_idempotency_key
from app.core.config import settings
from app.models.models import User, Order, OrderItem, Product, OrderStatus, UserRole
from app.schemas.schemas import OrderCreate, OrderResponse, DashboardStats

router = APIRouter(prefix="/orders", tags=["orders"])

# Initialize Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    order_data: OrderCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new order and initiate Stripe payment"""
    tenant = require_tenant()
    
    # Validate user is patient
    if current_user.role != UserRole.PATIENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only patients can create orders"
        )
    
    # Calculate total and validate products
    total_amount = 0.0
    order_items_data = []
    
    for item_data in order_data.items:
        result = await db.execute(
            select(Product).where(
                and_(
                    Product.id == item_data.product_id,
                    Product.tenant_id == tenant.id,
                    Product.is_active == True
                )
            )
        )
        product = result.scalar_one_or_none()
        
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product {item_data.product_id} not found or inactive"
            )
        
        item_total = product.price * item_data.quantity
        total_amount += item_total
        
        order_items_data.append({
            "product": product,
            "quantity": item_data.quantity,
            "unit_price": product.price,
            "total_price": item_total
        })
    
    if total_amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid order total"
        )
    
    # Generate invoice number
    invoice_number = f"INV-{datetime.utcnow().strftime('%Y%m%d')}-{UUID(int=0).hex[:8].upper()}"
    
    # Generate idempotency key for Stripe
    idempotency_key = generate_idempotency_key()
    
    # Create Stripe Payment Intent
    try:
        payment_intent = stripe.PaymentIntent.create(
            amount=int(total_amount * 100),  # Convert to cents
            currency="usd",
            metadata={
                "tenant_id": str(tenant.id),
                "user_id": str(current_user.id),
                "invoice_number": invoice_number
            },
            idempotency_key=idempotency_key
        )
    except stripe.error.StripeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Payment processing error: {str(e)}"
        )
    
    # Create order
    order = Order(
        tenant_id=tenant.id,
        patient_id=current_user.id,
        total_amount=total_amount,
        status=OrderStatus.PENDING,
        stripe_payment_intent_id=payment_intent.id,
        invoice_number=invoice_number,
        idempotency_key=idempotency_key
    )
    
    db.add(order)
    await db.flush()  # Get order ID
    
    # Create order items
    for item_data in order_items_data:
        order_item = OrderItem(
            tenant_id=tenant.id,
            order_id=order.id,
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
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get orders for current user"""
    tenant = require_tenant()
    
    if current_user.role == UserRole.PATIENT:
        # Patients see their own orders
        result = await db.execute(
            select(Order).where(
                and_(
                    Order.tenant_id == tenant.id,
                    Order.patient_id == current_user.id
                )
            ).order_by(Order.created_at.desc()).offset(skip).limit(limit)
        )
    else:
        # Doctors and admins see all orders
        result = await db.execute(
            select(Order).where(
                Order.tenant_id == tenant.id
            ).order_by(Order.created_at.desc()).offset(skip).limit(limit)
        )
    
    orders = result.scalars().all()
    return orders


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific order"""
    tenant = require_tenant()
    
    result = await db.execute(
        select(Order).where(
            and_(
                Order.id == order_id,
                Order.tenant_id == tenant.id
            )
        )
    )
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    # Patients can only see their own orders
    if current_user.role == UserRole.PATIENT and order.patient_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this order"
        )
    
    return order


@router.post("/{order_id}/pay")
async def confirm_payment(
    order_id: UUID,
    payment_method_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Confirm payment for an order using Stripe"""
    tenant = require_tenant()
    
    result = await db.execute(
        select(Order).where(
            and_(
                Order.id == order_id,
                Order.tenant_id == tenant.id,
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
            detail=f"Order status is {order.status.value}, payment cannot be processed"
        )
    
    # Confirm payment with Stripe
    try:
        payment_intent = stripe.PaymentIntent.confirm(
            order.stripe_payment_intent_id,
            payment_method=payment_method_id
        )
    except stripe.error.StripeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Payment confirmation failed: {str(e)}"
        )
    
    # Update order based on payment status
    if payment_intent.status == "succeeded":
        order.status = OrderStatus.PAID
        order.stripe_charge_id = payment_intent.charges.data[0].id if payment_intent.charges.data else None
        order.stripe_receipt_url = payment_intent.charges.data[0].receipt_url if payment_intent.charges.data else None
        order.paid_at = datetime.utcnow()
        
        # Schedule order processing
        background_tasks.add_task(process_order_background, order_id)
    else:
        order.status = OrderStatus.CANCELLED
    
    await db.commit()
    await db.refresh(order)
    
    return {
        "order_id": str(order.id),
        "status": order.status.value,
        "payment_intent_status": payment_intent.status
    }


@router.post("/{order_id}/refund")
async def refund_order(
    order_id: UUID,
    refund_reason: str = "",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Refund an order (admin only)"""
    tenant = require_tenant()
    
    result = await db.execute(
        select(Order).where(
            and_(
                Order.id == order_id,
                Order.tenant_id == tenant.id
            )
        )
    )
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    if not order.stripe_charge_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No charge found to refund"
        )
    
    if order.refunded_amount >= order.total_amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order already fully refunded"
        )
    
    # Process refund with Stripe
    try:
        refund = stripe.Refund.create(
            charge=order.stripe_charge_id,
            reason="requested_by_customer" if refund_reason else None,
            metadata={"order_id": str(order.id)}
        )
    except stripe.error.StripeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Refund failed: {str(e)}"
        )
    
    # Update order
    order.refunded_amount = refund.amount / 100.0
    order.refund_reason = refund_reason
    order.status = OrderStatus.REFUNDED if order.refunded_amount >= order.total_amount else OrderStatus.PAID
    
    await db.commit()
    
    return {
        "order_id": str(order.id),
        "refund_amount": order.refunded_amount,
        "refund_id": refund.id
    }


@router.get("/stats/dashboard", response_model=DashboardStats)
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_doctor)
):
    """Get dashboard statistics"""
    tenant = require_tenant()
    
    # Get all orders for this tenant
    result = await db.execute(
        select(Order).where(Order.tenant_id == tenant.id)
    )
    orders = result.scalars().all()
    
    # Get all assessments for this tenant
    from app.models.models import Assessment
    result = await db.execute(
        select(Assessment).where(Assessment.tenant_id == tenant.id)
    )
    assessments = result.scalars().all()
    
    # Calculate stats
    total_revenue = sum(o.total_amount for o in orders if o.status == OrderStatus.PAID)
    total_orders = len(orders)
    total_assessments = len(assessments)
    pending_reviews = len([a for a in assessments if a.status in ["uploaded", "in_review"]])
    
    # Calculate monthly growth (simplified)
    one_month_ago = datetime.utcnow() - timedelta(days=30)
    monthly_orders = [o for o in orders if o.created_at >= one_month_ago]
    monthly_growth = (len(monthly_orders) / max(total_orders, 1)) * 100
    
    return DashboardStats(
        total_revenue=total_revenue,
        total_orders=total_orders,
        total_assessments=total_assessments,
        pending_reviews=pending_reviews,
        monthly_growth=round(monthly_growth, 2)
    )


async def process_order_background(order_id: UUID):
    """Background task to process order after payment"""
    from app.db.session import AsyncSessionLocal
    
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Order).where(Order.id == order_id)
        )
        order = result.scalar_one_or_none()
        
        if order and order.status == OrderStatus.PAID:
            order.status = OrderStatus.PROCESSING
            await db.commit()
