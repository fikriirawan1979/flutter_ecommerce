from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from app.db.session import get_db
from app.api.deps import get_current_user, get_current_active_user
from app.core.security import rate_limiter
from app.models.models import User, Assessment, AssessmentStatus, Order, UserRole, AssessmentImage
from app.schemas.schemas import (
    AssessmentCreate, AssessmentUpdate, AssessmentResponse,
    CephalometricMeasurements, AssessmentResult, ImageUploadResponse
)
from assessment_engine.cephalometric_engine import assess_dental_measurements
from app.services.ai_service import ai_service

router = APIRouter(prefix="/assessments", tags=["assessments"])

@router.post("/create", response_model=AssessmentResponse)
async def create_assessment(
    assessment_data: AssessmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new assessment for an order with tenant isolation"""
    # Verify order exists and belongs to user with tenant check
    order_result = await db.execute(
        select(Order).where(
            and_(
                Order.id == assessment_data.order_id,
                Order.patient_id == current_user.id,
                Order.tenant_id == current_user.tenant_id
            )
        )
    )
    order = order_result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    # Check if assessment already exists
    existing_result = await db.execute(
        select(Assessment).where(
            and_(
                Assessment.order_id == assessment_data.order_id,
                Assessment.tenant_id == current_user.tenant_id
            )
        )
    )
    if existing_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Assessment already exists for this order"
        )
    
    # Create assessment with tenant isolation
    assessment = Assessment(
        order_id=assessment_data.order_id,
        patient_id=current_user.id,
        tenant_id=current_user.tenant_id,
        status=AssessmentStatus.PENDING_UPLOAD
    )
    
    db.add(assessment)
    await db.commit()
    await db.refresh(assessment)
    
    return assessment

@router.get("/my-assessments", response_model=List[AssessmentResponse])
async def get_my_assessments(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get assessments for current user with tenant isolation"""
    result = await db.execute(
        select(Assessment).where(
            and_(
                Assessment.patient_id == current_user.id,
                Assessment.tenant_id == current_user.tenant_id
            )
        ).order_by(Assessment.created_at.desc())
    )
    assessments = result.scalars().all()
    return assessments

@router.get("/pending", response_model=List[AssessmentResponse])
async def get_pending_assessments(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get pending assessments (for doctors) with tenant isolation"""
    if current_user.role not in [UserRole.DOCTOR, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only doctors can view pending assessments"
        )
    
    result = await db.execute(
        select(Assessment).where(
            and_(
                Assessment.tenant_id == current_user.tenant_id,
                Assessment.status.in_([
                    AssessmentStatus.UPLOADED,
                    AssessmentStatus.AI_COMPLETED,
                    AssessmentStatus.IN_REVIEW
                ])
            )
        ).order_by(Assessment.created_at.desc())
    )
    assessments = result.scalars().all()
    return assessments

@router.post("/{assessment_id}/upload-image", response_model=ImageUploadResponse)
async def upload_assessment_image(
    assessment_id: UUID,
    file: UploadFile = File(...),
    image_type: str = "xray",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Upload an image for assessment with tenant isolation"""
    # Rate limiting for uploads
    upload_key = f"upload:{current_user.id}"
    if not rate_limiter.is_allowed(upload_key, max_requests=10, window_seconds=60):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Upload rate limit exceeded"
        )
    
    # Get assessment with tenant check
    result = await db.execute(
        select(Assessment).where(
            and_(
                Assessment.id == assessment_id,
                Assessment.tenant_id == current_user.tenant_id
            )
        )
    )
    assessment = result.scalar_one_or_none()
    
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found"
        )
    
    if assessment.patient_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to upload to this assessment"
        )
    
    # Validate file type
    allowed_types = {"image/jpeg", "image/png", "image/dicom", "application/dicom"}
    content_type = file.content_type or ""
    if content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type: {content_type}. Allowed: JPEG, PNG, DICOM"
        )
    
    # Validate file size (10MB max)
    max_size = 10 * 1024 * 1024  # 10MB
    file_content = await file.read()
    if len(file_content) > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File too large. Maximum size is 10MB"
        )
    
    # TODO: Implement actual file upload to MinIO/S3 with tenant isolation
    # Generate storage path with tenant prefix for isolation
    storage_path = f"{current_user.tenant_id}/{assessment_id}/{file.filename}"
    file_url = f"https://storage.dentalclinic.com/{storage_path}"
    
    # Create image record
    import hashlib
    image = AssessmentImage(
        assessment_id=assessment_id,
        tenant_id=current_user.tenant_id,
        file_url=file_url,
        file_name=file.filename,
        file_type=image_type,
        mime_type=content_type,
        file_size=len(file_content),
        checksum_sha256=hashlib.sha256(file_content).hexdigest(),
        storage_path=storage_path,
        validated=True
    )
    
    db.add(image)
    
    # Update assessment status
    assessment.status = AssessmentStatus.UPLOADED
    await db.commit()
    
    return ImageUploadResponse(
        id=assessment_id,
        file_url=file_url,
        file_name=file.filename,
        file_type=image_type,
        uploaded_at=datetime.utcnow()
    )

@router.post("/{assessment_id}/analyze", response_model=AssessmentResult)
async def analyze_assessment(
    assessment_id: UUID,
    measurements: CephalometricMeasurements,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Analyze assessment measurements using rule engine with tenant isolation"""
    # Verify doctor access
    if current_user.role not in [UserRole.DOCTOR, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only doctors can perform analysis"
        )
    
    # Get assessment with tenant check
    result = await db.execute(
        select(Assessment).where(
            and_(
                Assessment.id == assessment_id,
                Assessment.tenant_id == current_user.tenant_id
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
    measurement_dict = {
        'SNA': measurements.sna,
        'SNB': measurements.snb,
        'ANB': measurements.anb,
        'Overjet': measurements.overjet,
        'Overbite': measurements.overbite
    }
    
    analysis_result = assess_dental_measurements(measurement_dict)
    
    # Update assessment with results
    assessment.sna = measurements.sna
    assessment.snb = measurements.snb
    assessment.anb = measurements.anb
    assessment.overjet = measurements.overjet
    assessment.overbite = measurements.overbite
    assessment.skeletal_class = analysis_result['skeletal_class']
    assessment.severity = analysis_result['severity']
    assessment.treatment_suggestion = analysis_result['treatment_suggestion']
    assessment.confidence_score = analysis_result['confidence_score']
    assessment.status = AssessmentStatus.IN_REVIEW
    assessment.doctor_id = current_user.id
    
    await db.commit()
    await db.refresh(assessment)
    
    return AssessmentResult(
        skeletal_class=analysis_result['skeletal_class'],
        severity=analysis_result['severity'],
        treatment_suggestion=analysis_result['treatment_suggestion'],
        confidence_score=analysis_result['confidence_score']
    )


@router.post("/{assessment_id}/ai-analyze")
async def ai_analyze_assessment(
    assessment_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Submit assessment for AI analysis
    Requires uploaded images
    """
    # Verify assessment belongs to user or user is doctor
    result = await db.execute(
        select(Assessment).where(
            and_(
                Assessment.id == assessment_id,
                Assessment.tenant_id == current_user.tenant_id
            )
        )
    )
    assessment = result.scalar_one_or_none()
    
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found"
        )
    
    # Only patient who owns it or doctors can trigger AI analysis
    if (assessment.patient_id != current_user.id and 
        current_user.role not in [UserRole.DOCTOR, UserRole.ADMIN]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )
    
    # Check if images exist
    image_result = await db.execute(
        select(AssessmentImage).where(
            and_(
                AssessmentImage.assessment_id == assessment_id,
                AssessmentImage.tenant_id == current_user.tenant_id
            )
        )
    )
    images = image_result.scalars().all()
    
    if not images:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No images uploaded for analysis"
        )
    
    # Update status
    assessment.status = AssessmentStatus.AI_PROCESSING
    assessment.ai_started_at = datetime.utcnow()
    await db.commit()
    
    # Submit to AI service
    try:
        # Initialize AI service if not already
        if not ai_service._initialized:
            await ai_service.initialize()
        
        job_id = await ai_service.submit_analysis(
            assessment_id=assessment_id,
            tenant_id=current_user.tenant_id,
            image_paths=[img.storage_path for img in images],
            priority=5
        )
        
        return {
            "message": "AI analysis submitted",
            "job_id": job_id,
            "status": "processing"
        }
        
    except Exception as e:
        assessment.status = AssessmentStatus.UPLOADED
        assessment.ai_error_message = str(e)
        await db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI analysis submission failed: {str(e)}"
        )


@router.get("/{assessment_id}/ai-status")
async def get_ai_analysis_status(
    assessment_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get AI analysis status for an assessment"""
    result = await db.execute(
        select(Assessment).where(
            and_(
                Assessment.id == assessment_id,
                Assessment.tenant_id == current_user.tenant_id
            )
        )
    )
    assessment = result.scalar_one_or_none()
    
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found"
        )
    
    # Verify access
    if (assessment.patient_id != current_user.id and 
        current_user.role not in [UserRole.DOCTOR, UserRole.ADMIN]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )
    
    return {
        "assessment_id": str(assessment_id),
        "status": assessment.status.value,
        "ai_analysis": assessment.ai_analysis,
        "ai_confidence_score": assessment.ai_confidence_score,
        "ai_model_version": assessment.ai_model_version,
        "ai_started_at": assessment.ai_started_at,
        "ai_completed_at": assessment.ai_completed_at,
        "ai_error_message": assessment.ai_error_message
    }

@router.post("/{assessment_id}/complete")
async def complete_assessment(
    assessment_id: UUID,
    diagnosis_notes: str = "",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Mark assessment as completed with tenant isolation"""
    if current_user.role not in [UserRole.DOCTOR, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only doctors can complete assessments"
        )
    
    result = await db.execute(
        select(Assessment).where(
            and_(
                Assessment.id == assessment_id,
                Assessment.tenant_id == current_user.tenant_id
            )
        )
    )
    assessment = result.scalar_one_or_none()
    
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found"
        )
    
    assessment.status = AssessmentStatus.COMPLETED
    assessment.diagnosis_notes = diagnosis_notes
    assessment.completed_at = datetime.utcnow()
    assessment.doctor_id = current_user.id
    
    await db.commit()
    
    return {"message": "Assessment completed successfully"}


@router.get("/{assessment_id}/report")
async def generate_assessment_report(
    assessment_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Generate PDF report for assessment with tenant isolation"""
    result = await db.execute(
        select(Assessment).where(
            and_(
                Assessment.id == assessment_id,
                Assessment.tenant_id == current_user.tenant_id
            )
        )
    )
    assessment = result.scalar_one_or_none()
    
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found"
        )
    
    # Verify access - patient who owns it or doctors/admins
    if (assessment.patient_id != current_user.id and 
        current_user.role not in [UserRole.DOCTOR, UserRole.ADMIN]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this report"
        )
    
    if assessment.status != AssessmentStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Assessment not yet completed"
        )
    
    # TODO: Generate PDF using WeasyPrint or similar
    return {
        "message": "Report generation endpoint",
        "assessment_id": str(assessment_id),
        "download_url": f"/api/v1/assessments/{assessment_id}/download-report",
        "report_data": {
            "skeletal_class": assessment.skeletal_class,
            "severity": assessment.severity,
            "treatment_suggestion": assessment.treatment_suggestion,
            "diagnosis_notes": assessment.diagnosis_notes,
            "completed_at": assessment.completed_at
        }
    }


@router.get("/{assessment_id}", response_model=AssessmentResponse)
async def get_assessment(
    assessment_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get assessment details with tenant isolation"""
    result = await db.execute(
        select(Assessment).where(
            and_(
                Assessment.id == assessment_id,
                Assessment.tenant_id == current_user.tenant_id
            )
        )
    )
    assessment = result.scalar_one_or_none()
    
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found"
        )
    
    # Verify access
    if (assessment.patient_id != current_user.id and 
        current_user.role not in [UserRole.DOCTOR, UserRole.ADMIN]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )
    
    return assessment