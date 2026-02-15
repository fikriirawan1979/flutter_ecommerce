"""
Stripe Webhook endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
import stripe
import json
import logging

from app.db.session import get_db
from app.core.security import verify_webhook_signature
from app.core.config import settings
from app.models.models import Order, OrderStatus

router = APIRouter(prefix="/webhooks/stripe", tags=["webhooks"])
logger = logging.getLogger(__name__)


@router.post("/")
async def stripe_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Handle Stripe webhook events
    
    Supported events:
    - payment_intent.succeeded
    - payment_intent.payment_failed
    - charge.refunded
    - customer.subscription.created
    - customer.subscription.updated
    - customer.subscription.deleted
    """
    
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    
    # Verify webhook signature
    if not verify_webhook_signature(payload, sig_header, settings.STRIPE_WEBHOOK_SECRET):
        logger.warning("Invalid webhook signature")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid webhook signature"
        )
    
    # Parse event
    try:
        event = stripe.Event.construct_from(
            json.loads(payload), stripe.api_key
        )
    except ValueError as e:
        logger.error(f"Invalid webhook payload: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid payload"
        )
    
    # Handle different event types
    event_type = event["type"]
    logger.info(f"Received Stripe webhook: {event_type}")
    
    try:
        if event_type == "payment_intent.succeeded":
            await handle_payment_succeeded(event["data"]["object"], db, background_tasks)
        elif event_type == "payment_intent.payment_failed":
            await handle_payment_failed(event["data"]["object"], db)
        elif event_type == "charge.refunded":
            await handle_charge_refunded(event["data"]["object"], db)
        elif event_type == "invoice.payment_succeeded":
            await handle_invoice_payment_succeeded(event["data"]["object"], db)
        elif event_type == "invoice.payment_failed":
            await handle_invoice_payment_failed(event["data"]["object"], db)
        else:
            logger.info(f"Unhandled event type: {event_type}")
    except Exception as e:
        logger.error(f"Error processing webhook {event_type}: {e}", exc_info=True)
        # Don't raise - we want to acknowledge receipt even if processing fails
    
    return {"status": "received"}


async def handle_payment_succeeded(payment_intent: dict, db: AsyncSession, background_tasks: BackgroundTasks):
    """Handle successful payment"""
    payment_intent_id = payment_intent["id"]
    
    logger.info(f"Payment succeeded: {payment_intent_id}")
    
    # Find order by payment intent ID
    result = await db.execute(
        select(Order).where(Order.stripe_payment_intent_id == payment_intent_id)
    )
    order = result.scalar_one_or_none()
    
    if order:
        # Update order status
        if order.status == OrderStatus.PENDING:
            order.status = OrderStatus.PAID
            
            # Store charge info
            if "charges" in payment_intent and payment_intent["charges"]["data"]:
                charge = payment_intent["charges"]["data"][0]
                order.stripe_charge_id = charge["id"]
                order.stripe_receipt_url = charge.get("receipt_url")
            
            from datetime import datetime
            order.paid_at = datetime.utcnow()
            
            await db.commit()
            logger.info(f"Order {order.id} marked as paid")
            
            # Schedule background processing
            background_tasks.add_task(process_order_after_payment, order.id)


async def handle_payment_failed(payment_intent: dict, db: AsyncSession):
    """Handle failed payment"""
    payment_intent_id = payment_intent["id"]
    
    logger.warning(f"Payment failed: {payment_intent_id}")
    
    # Find order by payment intent ID
    result = await db.execute(
        select(Order).where(Order.stripe_payment_intent_id == payment_intent_id)
    )
    order = result.scalar_one_or_none()
    
    if order:
        order.status = OrderStatus.CANCELLED
        await db.commit()
        logger.info(f"Order {order.id} cancelled due to payment failure")


async def handle_charge_refunded(charge: dict, db: AsyncSession):
    """Handle charge refund"""
    charge_id = charge["id"]
    amount_refunded = charge["amount_refunded"] / 100.0  # Convert from cents
    
    logger.info(f"Charge refunded: {charge_id}, amount: ${amount_refunded}")
    
    # Find order by charge ID
    result = await db.execute(
        select(Order).where(Order.stripe_charge_id == charge_id)
    )
    order = result.scalar_one_or_none()
    
    if order:
        order.refunded_amount = amount_refunded
        if amount_refunded >= order.total_amount:
            order.status = OrderStatus.REFUNDED
        
        await db.commit()
        logger.info(f"Order {order.id} updated with refund")


async def handle_invoice_payment_succeeded(invoice: dict, db: AsyncSession):
    """Handle successful invoice payment (for subscriptions)"""
    logger.info(f"Invoice payment succeeded: {invoice['id']}")
    # Implement subscription billing logic here


async def handle_invoice_payment_failed(invoice: dict, db: AsyncSession):
    """Handle failed invoice payment (for subscriptions)"""
    logger.warning(f"Invoice payment failed: {invoice['id']}")
    # Implement subscription billing logic here


async def process_order_after_payment(order_id: UUID):
    """Background task to process order after successful payment"""
    from app.db.session import AsyncSessionLocal
    from app.models.models import OrderStatus
    
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Order).where(Order.id == order_id)
        )
        order = result.scalar_one_or_none()
        
        if order and order.status == OrderStatus.PAID:
            # Move to processing
            order.status = OrderStatus.PROCESSING
            await db.commit()
            logger.info(f"Order {order_id} moved to processing status")
