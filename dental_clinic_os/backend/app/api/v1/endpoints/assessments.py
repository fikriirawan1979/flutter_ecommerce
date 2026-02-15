from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List
from uuid import UUID

from app.db.session import get_db
from app.core.security import get_current_user, get_current_active_user
from app.models.models import User, Assessment, AssessmentStatus, Order, UserRole
from app.schemas.schemas import (
    AssessmentCreate, AssessmentUpdate, AssessmentResponse,
    CephalometricMeasurements, AssessmentResult, ImageUploadResponse
)
from assessment_engine.cephalometric_engine import assess_dental_measurements

router = APIRouter(prefix="/assessments", tags=["assessments"])

@router.post("/create", response_model=AssessmentResponse)
async def create_assessment(
    assessment_data: AssessmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new assessment for an order"""
    # Verify order exists and belongs to user
    order_result = await db.execute(
        select(Order).where(
            and_(
                Order.id == assessment_data.order_id,
                Order.patient_id == current_user.id
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
        select(Assessment).where(Assessment.order_id == assessment_data.order_id)
    )
    if existing_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Assessment already exists for this order"
        )
    
    # Create assessment
    assessment = Assessment(
        order_id=assessment_data.order_id,
        patient_id=current_user.id,
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
    """Get assessments for current user"""
    result = await db.execute(
        select(Assessment).where(Assessment.patient_id == current_user.id)
    )
    assessments = result.scalars().all()
    return assessments

@router.get("/pending", response_model=List[AssessmentResponse])
async def get_pending_assessments(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get pending assessments (for doctors)"""
    if current_user.role not in [UserRole.DOCTOR, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only doctors can view pending assessments"
        )
    
    result = await db.execute(
        select(Assessment).where(
            Assessment.status.in_([
                AssessmentStatus.UPLOADED,
                AssessmentStatus.IN_REVIEW
            ])
        )
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
    """Upload an image for assessment"""
    from app.services.minio_service import upload_assessment_image
    from app.models.models import AssessmentImage
    from app.middleware.tenant_middleware import get_current_tenant
    
    tenant = get_current_tenant()
    
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
    
    if assessment.patient_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to upload to this assessment"
        )
    
    # Read file content
    file_content = await file.read()
    
    # Upload to MinIO
    upload_result = await upload_assessment_image(
        file_content,
        file.filename,
        str(assessment_id),
        image_type,
        str(tenant.id)
    )
    
    if not upload_result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"File upload failed: {upload_result.get('error', 'Unknown error')}"
        )
    
    # Create image record
    from datetime import datetime
    image_record = AssessmentImage(
        tenant_id=tenant.id,
        assessment_id=assessment_id,
        file_url=upload_result["file_url"],
        file_name=file.filename,
        file_type=image_type,
        mime_type=file.content_type or "application/octet-stream",
        file_size=upload_result["file_size"],
        checksum_sha256=upload_result["checksum"],
        storage_path=upload_result["storage_path"],
        validated=True,
        uploaded_at=datetime.utcnow()
    )
    
    db.add(image_record)
    
    # Update assessment status
    assessment.status = AssessmentStatus.UPLOADED
    await db.commit()
    await db.refresh(assessment)
    
    return ImageUploadResponse(
        id=assessment_id,
        file_url=upload_result["file_url"],
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
    """Analyze assessment measurements using rule engine"""
    # Verify doctor access
    if current_user.role not in [UserRole.DOCTOR, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only doctors can perform analysis"
        )
    
    # Get assessment
    result = await db.execute(
        select(Assessment).where(Assessment.id == assessment_id)
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

@router.post("/{assessment_id}/complete")
async def complete_assessment(
    assessment_id: UUID,
    diagnosis_notes: str = "",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Mark assessment as completed"""
    if current_user.role not in [UserRole.DOCTOR, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only doctors can complete assessments"
        )
    
    result = await db.execute(
        select(Assessment).where(Assessment.id == assessment_id)
    )
    assessment = result.scalar_one_or_none()
    
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found"
        )
    
    from datetime import datetime
    assessment.status = AssessmentStatus.COMPLETED
    assessment.diagnosis_notes = diagnosis_notes
    assessment.completed_at = datetime.utcnow()
    
    await db.commit()
    
    return {"message": "Assessment completed successfully"}

@router.get("/{assessment_id}/report")
async def generate_assessment_report(
    assessment_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Generate PDF report for assessment"""
    result = await db.execute(
        select(Assessment).where(
            and_(
                Assessment.id == assessment_id,
                Assessment.patient_id == current_user.id
            )
        )
    )
    assessment = result.scalar_one_or_none()
    
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found"
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
        "download_url": f"/api/v1/assessments/{assessment_id}/download-report"
    }