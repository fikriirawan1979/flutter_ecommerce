"""
Stripe payment processing endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import Optional
from uuid import UUID
from datetime import datetime
import stripe
import json
import logging

from app.db.session import get_db
from app.core.security import get_current_user, get_current_admin, verify_webhook_signature
from app.core.config import settings
from app.models.models import User, Order, UserRole, OrderStatus
from app.schemas.schemas import OrderResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/payments", tags=["payments"])

# Initialize Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


@router.post("/create-payment-intent")
async def create_payment_intent(
    order_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a Stripe PaymentIntent for an order.
    
    This is a hardened payment flow that:
    - Validates order ownership
    - Checks order status
    - Creates idempotent payment intent
    - Handles errors properly
    """
    # Get order
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
    
    # Check if order is in correct state
    if order.status not in [OrderStatus.PENDING]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Order is {order.status.value}, cannot create payment"
        )
    
    # Check if payment already exists
    if order.stripe_payment_intent_id:
        # Return existing payment intent
        try:
            payment_intent = stripe.PaymentIntent.retrieve(order.stripe_payment_intent_id)
            return {
                "client_secret": payment_intent.client_secret,
                "payment_intent_id": payment_intent.id,
                "amount": payment_intent.amount,
                "currency": payment_intent.currency
            }
        except stripe.error.StripeError as e:
            logger.error(f"Error retrieving payment intent: {e}")
            # Fall through to create new one
    
    try:
        # Create payment intent with amount in cents
        amount_cents = int(order.total_amount * 100)
        
        payment_intent = stripe.PaymentIntent.create(
            amount=amount_cents,
            currency="usd",
            metadata={
                "order_id": str(order.id),
                "tenant_id": str(current_user.tenant_id),
                "user_id": str(current_user.id),
                "invoice_number": order.invoice_number
            },
            idempotency_key=order.idempotency_key
        )
        
        # Update order with payment intent ID
        order.stripe_payment_intent_id = payment_intent.id
        order.updated_at = datetime.utcnow()
        await db.commit()
        
        return {
            "client_secret": payment_intent.client_secret,
            "payment_intent_id": payment_intent.id,
            "amount": payment_intent.amount,
            "currency": payment_intent.currency
        }
        
    except stripe.error.CardError as e:
        logger.error(f"Card error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Card error: {str(e)}"
        )
    except stripe.error.RateLimitError:
        logger.error("Stripe rate limit error")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests to payment provider"
        )
    except stripe.error.InvalidRequestError as e:
        logger.error(f"Invalid request: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid request: {str(e)}"
        )
    except stripe.error.AuthenticationError:
        logger.error("Stripe authentication error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Payment provider authentication failed"
        )
    except stripe.error.APIConnectionError:
        logger.error("Stripe API connection error")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Payment provider connection failed"
        )
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Payment processing failed"
        )


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(..., alias="Stripe-Signature"),
    db: AsyncSession = Depends(get_db)
):
    """
    Handle Stripe webhooks for payment events.
    
    This endpoint:
    - Verifies webhook signature
    - Handles payment_intent.succeeded
    - Handles payment_intent.payment_failed
    - Updates order status
    - Logs all events
    """
    if not settings.STRIPE_WEBHOOK_SECRET:
        logger.error("STRIPE_WEBHOOK_SECRET not configured")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Webhook not configured"
        )
    
    # Get raw body
    payload = await request.body()
    
    # Verify signature
    try:
        event = stripe.Webhook.construct_event(
            payload,
            stripe_signature,
            settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        logger.error(f"Invalid payload: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid payload"
        )
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Invalid signature: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid signature"
        )
    
    # Handle event
    event_type = event["type"]
    logger.info(f"Processing webhook event: {event_type}")
    
    try:
        if event_type == "payment_intent.succeeded":
            await handle_payment_succeeded(event["data"]["object"], db)
        elif event_type == "payment_intent.payment_failed":
            await handle_payment_failed(event["data"]["object"], db)
        elif event_type == "payment_intent.canceled":
            await handle_payment_canceled(event["data"]["object"], db)
        else:
            logger.info(f"Unhandled event type: {event_type}")
        
        return {"status": "success"}
        
    except Exception as e:
        logger.error(f"Error processing webhook: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Webhook processing failed"
        )


async def handle_payment_succeeded(payment_intent: dict, db: AsyncSession):
    """Handle successful payment"""
    order_id = payment_intent["metadata"].get("order_id")
    
    if not order_id:
        logger.error("Payment intent missing order_id in metadata")
        return
    
    from uuid import UUID
    result = await db.execute(
        select(Order).where(Order.id == UUID(order_id))
    )
    order = result.scalar_one_or_none()
    
    if not order:
        logger.error(f"Order {order_id} not found")
        return
    
    # Update order
    order.status = OrderStatus.PAID
    order.stripe_payment_intent_id = payment_intent["id"]
    order.stripe_charge_id = payment_intent.get("charges", {}).get("data", [{}])[0].get("id")
    order.paid_at = datetime.utcnow()
    
    logger.info(f"Order {order_id} marked as paid")
    await db.commit()


async def handle_payment_failed(payment_intent: dict, db: AsyncSession):
    """Handle failed payment"""
    order_id = payment_intent["metadata"].get("order_id")
    
    if not order_id:
        logger.error("Payment intent missing order_id in metadata")
        return
    
    from uuid import UUID
    result = await db.execute(
        select(Order).where(Order.id == UUID(order_id))
    )
    order = result.scalar_one_or_none()
    
    if not order:
        logger.error(f"Order {order_id} not found")
        return
    
    # Update order status to indicate payment failed
    order.status = OrderStatus.PENDING  # Keep pending for retry
    order.stripe_payment_intent_id = payment_intent["id"]
    
    logger.warning(f"Order {order_id} payment failed")
    await db.commit()


async def handle_payment_canceled(payment_intent: dict, db: AsyncSession):
    """Handle canceled payment"""
    order_id = payment_intent["metadata"].get("order_id")
    
    if not order_id:
        return
    
    from uuid import UUID
    result = await db.execute(
        select(Order).where(Order.id == UUID(order_id))
    )
    order = result.scalar_one_or_none()
    
    if order:
        order.status = OrderStatus.CANCELLED
        order.stripe_payment_intent_id = payment_intent["id"]
        await db.commit()
    
    logger.info(f"Order {order_id} payment canceled")


@router.post("/{order_id}/refund")
async def refund_payment(
    order_id: UUID,
    reason: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Process a refund for an order"""
    # Get order
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
    
    if not order.stripe_payment_intent_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No payment found for this order"
        )
    
    if order.status == OrderStatus.REFUNDED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order already refunded"
        )
    
    try:
        # Create refund
        refund = stripe.Refund.create(
            payment_intent=order.stripe_payment_intent_id,
            reason="requested_by_customer" if reason else None,
            metadata={
                "order_id": str(order.id),
                "tenant_id": str(current_user.tenant_id),
                "refunded_by": str(current_user.id)
            }
        )
        
        # Update order
        order.status = OrderStatus.REFUNDED
        order.refunded_amount = order.total_amount
        order.refund_reason = reason
        order.updated_at = datetime.utcnow()
        
        await db.commit()
        
        return {
            "refund_id": refund.id,
            "amount": refund.amount,
            "currency": refund.currency,
            "status": refund.status
        }
        
    except stripe.error.StripeError as e:
        logger.error(f"Refund error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Refund failed: {str(e)}"
        )


@router.get("/{order_id}/status")
async def get_payment_status(
    order_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get payment status for an order"""
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
    
    # If payment intent exists, get latest status from Stripe
    stripe_status = None
    if order.stripe_payment_intent_id:
        try:
            payment_intent = stripe.PaymentIntent.retrieve(order.stripe_payment_intent_id)
            stripe_status = payment_intent.status
        except stripe.error.StripeError:
            pass
    
    return {
        "order_id": str(order.id),
        "order_status": order.status.value,
        "total_amount": order.total_amount,
        "stripe_payment_intent_id": order.stripe_payment_intent_id,
        "stripe_status": stripe_status,
        "paid_at": order.paid_at,
        "refunded_amount": order.refunded_amount
    }
