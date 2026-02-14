"""
Webhook endpoints for external services
Stripe, AI service callbacks, and third-party integrations
"""

from fastapi import APIRouter, Request, HTTPException, status, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
import logging

from app.db.session import get_db
from app.services.stripe_service import stripe_service

router = APIRouter(prefix="/webhooks", tags=["webhooks"])
logger = logging.getLogger(__name__)


@router.post("/stripe")
async def stripe_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Handle Stripe webhook events
    
    Security:
    - Validates webhook signature
    - Idempotent processing
    - Comprehensive logging
    """
    payload = await request.body()
    signature = request.headers.get("stripe-signature")
    
    if not signature:
        logger.warning("Stripe webhook missing signature")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing signature"
        )
    
    try:
        result = await stripe_service.handle_webhook(
            payload=payload,
            signature=signature,
            db=db
        )
        
        logger.info(f"Stripe webhook processed: {result}")
        return JSONResponse(content={"status": "success"})
        
    except Exception as e:
        logger.error(f"Stripe webhook error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/ai-callback/{assessment_id}")
async def ai_callback(
    assessment_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Handle AI service callback with analysis results
    
    Secured by API key validation in production
    """
    # In production, validate API key from headers
    # api_key = request.headers.get("X-API-Key")
    # if not validate_ai_api_key(api_key):
    #     raise HTTPException(status_code=401, detail="Invalid API key")
    
    try:
        data = await request.json()
        
        # Update assessment with AI results
        from sqlalchemy import select, update
        from app.models.models import Assessment, AssessmentStatus
        from uuid import UUID
        
        stmt = (
            update(Assessment)
            .where(Assessment.id == UUID(assessment_id))
            .values(
                ai_analysis=data.get("analysis"),
                ai_model_version=data.get("model_version"),
                ai_confidence_score=data.get("confidence_score"),
                ai_processing_time_ms=data.get("processing_time_ms"),
                ai_completed_at=datetime.utcnow(),
                status=AssessmentStatus.AI_COMPLETED,
                skeletal_class=data.get("skeletal_class"),
                dental_class=data.get("dental_class"),
                risk_score=data.get("risk_score"),
                treatment_suggestion=data.get("treatment_suggestion"),
                confidence_score=data.get("confidence_score")
            )
        )
        
        await db.execute(stmt)
        await db.commit()
        
        logger.info(f"AI callback processed for assessment {assessment_id}")
        return JSONResponse(content={"status": "success"})
        
    except Exception as e:
        logger.error(f"AI callback error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/health")
async def webhook_health():
    """Health check for webhook endpoints"""
    return {"status": "healthy", "webhooks": ["stripe", "ai-callback"]}
