"""
AI Analysis API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from uuid import UUID
from datetime import datetime
import logging

from app.db.session import get_db
from app.core.security import get_current_user, get_current_doctor, require_tenant
from app.models.models import User, Assessment, AssessmentStatus, UserRole
from app.services.ai_service import ai_service, AnalysisResult
from app.schemas.schemas import AssessmentResult
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/ai", tags=["ai-analysis"])
logger = logging.getLogger(__name__)


class AIAnalysisResponse(BaseModel):
    """Response from AI analysis"""
    success: bool
    assessment_id: UUID
    measurements: dict
    skeletal_class: Optional[str] = None
    severity: Optional[str] = None
    confidence: float
    model_version: str
    processing_time_ms: int
    error_message: Optional[str] = None
    findings: Optional[list] = None
    recommendations: Optional[list] = None


@router.post("/assessments/{assessment_id}/analyze-xray", response_model=AIAnalysisResponse)
async def analyze_xray_for_assessment(
    assessment_id: UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_doctor)
):
    """
    Analyze X-ray image using AI
    
    This endpoint triggers AI-powered analysis of uploaded X-ray images.
    The analysis automatically detects anatomical landmarks and extracts
    cephalometric measurements.
    """
    tenant = require_tenant()
    
    # Get assessment
    result = await db.execute(
        select(Assessment).where(
            and_(
                Assessment.id == assessment_id,
                Assessment.tenant_id == tenant.id
            )
        )
    )
    assessment = result.scalar_one_or_none()
    
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found"
        )
    
    # Check if assessment has images
    if not assessment.images:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No images found for this assessment"
        )
    
    # Get latest X-ray image
    xray_image = None
    for image in assessment.images:
        if image.file_type in ["xray", "cephalometric"]:
            xray_image = image
            break
    
    if not xray_image:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No X-ray or cephalometric image found"
        )
    
    # Update assessment status
    assessment.status = AssessmentStatus.AI_PROCESSING
    assessment.ai_started_at = datetime.utcnow()
    assessment.ai_model_version = ai_service.model_version
    await db.commit()
    
    try:
        # Perform AI analysis
        analysis_result = await ai_service.analyze_xray(xray_image.storage_path)
        
        if not analysis_result.success:
            # Update with error
            assessment.status = AssessmentStatus.UPLOADED
            assessment.ai_error_message = analysis_result.error_message
            assessment.ai_retry_count += 1
            assessment.ai_completed_at = datetime.utcnow()
            await db.commit()
            
            return AIAnalysisResponse(
                success=False,
                assessment_id=assessment_id,
                measurements={},
                confidence=0.0,
                model_version=ai_service.model_version,
                processing_time_ms=analysis_result.processing_time_ms,
                error_message=analysis_result.error_message
            )
        
        # Update assessment with AI results
        assessment.ai_analysis = {
            "measurements": analysis_result.measurements,
            "landmarks": analysis_result.landmarks,
            "confidence": analysis_result.confidence,
            "model_version": analysis_result.model_version,
            "processing_time_ms": analysis_result.processing_time_ms
        }
        assessment.ai_confidence_score = analysis_result.confidence
        assessment.ai_processing_time_ms = analysis_result.processing_time_ms
        
        # Extract key measurements
        assessment.sna = analysis_result.measurements.get("SNA")
        assessment.snb = analysis_result.measurements.get("SNB")
        assessment.anb = analysis_result.measurements.get("ANB")
        assessment.overjet = analysis_result.measurements.get("Overjet")
        assessment.overbite = analysis_result.measurements.get("Overbite")
        assessment.additional_measurements = {
            k: v for k, v in analysis_result.measurements.items()
            if k not in ["SNA", "SNB", "ANB", "Overjet", "Overbite"]
        }
        
        # Get classification from rule engine
        from assessment_engine.cephalometric_engine import assess_dental_measurements
        classification_result = assess_dental_measurements(analysis_result.measurements)
        
        assessment.skeletal_class = classification_result['skeletal_class']
        assessment.severity = classification_result['severity']
        assessment.treatment_suggestion = classification_result['treatment_suggestion']
        assessment.confidence_score = classification_result['confidence_score']
        
        # Complete AI processing
        assessment.status = AssessmentStatus.AI_COMPLETED
        assessment.ai_completed_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(assessment)
        
        # Generate report
        report = ai_service.generate_report(
            analysis_result.measurements,
            analysis_result.landmarks
        )
        
        return AIAnalysisResponse(
            success=True,
            assessment_id=assessment_id,
            measurements=analysis_result.measurements,
            skeletal_class=assessment.skeletal_class,
            severity=assessment.severity,
            confidence=analysis_result.confidence,
            model_version=analysis_result.model_version,
            processing_time_ms=analysis_result.processing_time_ms,
            findings=report.get("findings"),
            recommendations=report.get("recommendations")
        )
        
    except Exception as e:
        logger.error(f"AI analysis failed for assessment {assessment_id}: {e}", exc_info=True)
        
        # Update assessment status
        assessment.status = AssessmentStatus.UPLOADED
        assessment.ai_error_message = str(e)
        assessment.ai_retry_count += 1
        assessment.ai_completed_at = datetime.utcnow()
        await db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI analysis failed: {str(e)}"
        )


@router.post("/assessments/{assessment_id}/analyze-manual")
async def analyze_manual_measurements(
    assessment_id: UUID,
    measurements: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_doctor)
):
    """
    Analyze manually entered measurements
    
    This endpoint allows doctors to manually enter cephalometric measurements
    and get automated classification and treatment suggestions.
    """
    tenant = require_tenant()
    
    # Get assessment
    result = await db.execute(
        select(Assessment).where(
            and_(
                Assessment.id == assessment_id,
                Assessment.tenant_id == tenant.id
            )
        )
    )
    assessment = result.scalar_one_or_none()
    
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found"
        )
    
    # Run assessment engine
    from assessment_engine.cephalometric_engine import assess_dental_measurements
    
    # Convert measurement keys to match expected format
    measurement_dict = {
        'SNA': measurements.get('SNA') or measurements.get('sna'),
        'SNB': measurements.get('SNB') or measurements.get('snb'),
        'ANB': measurements.get('ANB') or measurements.get('anb'),
        'Overjet': measurements.get('Overjet') or measurements.get('overjet'),
        'Overbite': measurements.get('Overbite') or measurements.get('overbite')
    }
    
    analysis_result = assess_dental_measurements(measurement_dict)
    
    # Update assessment
    assessment.sna = measurement_dict['SNA']
    assessment.snb = measurement_dict['SNB']
    assessment.anb = measurement_dict['ANB']
    assessment.overjet = measurement_dict['Overjet']
    assessment.overbite = measurement_dict['Overbite']
    assessment.skeletal_class = analysis_result['skeletal_class']
    assessment.severity = analysis_result['severity']
    assessment.treatment_suggestion = analysis_result['treatment_suggestion']
    assessment.confidence_score = analysis_result['confidence_score']
    assessment.status = AssessmentStatus.IN_REVIEW
    assessment.doctor_id = current_user.id
    
    await db.commit()
    await db.refresh(assessment)
    
    return {
        "assessment_id": str(assessment_id),
        "measurements": measurement_dict,
        "skeletal_class": analysis_result['skeletal_class'],
        "severity": analysis_result['severity'],
        "treatment_suggestion": analysis_result['treatment_suggestion'],
        "confidence_score": analysis_result['confidence_score'],
        "detailed_analysis": analysis_result.get('detailed_analysis', {})
    }


@router.get("/models/info")
async def get_model_info(current_user: User = Depends(get_current_user)):
    """Get information about AI models"""
    return {
        "model_version": ai_service.model_version,
        "model_loaded": ai_service.model_loaded,
        "model_path": str(ai_service.model_path),
        "supported_image_types": ["xray", "cephalometric", "panoramic"],
        "supported_formats": [".jpg", ".jpeg", ".png", ".dcm", ".dicom"]
    }
