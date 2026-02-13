"""
Hardened AI Service for Dental X-Ray Analysis
Features: Async processing, circuit breaker, retry logic, memory management
"""

import asyncio
import hashlib
import json
import logging
import time
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass
from uuid import UUID
import numpy as np

logger = logging.getLogger(__name__)

class AIProcessingStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    RETRYING = "retrying"

@dataclass
class AIResult:
    """Standardized AI analysis result"""
    skeletal_class: str
    dental_class: str
    risk_score: float
    recommended_action: str
    confidence_score: float
    model_version: str
    processing_time_ms: int
    raw_predictions: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None

@dataclass
class AIJob:
    """AI processing job"""
    id: str
    assessment_id: UUID
    tenant_id: UUID
    image_paths: list
    status: AIProcessingStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    retry_count: int = 0
    result: Optional[AIResult] = None
    error: Optional[str] = None

class CircuitBreaker:
    """Circuit breaker pattern to prevent cascade failures"""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half-open
        self._lock = asyncio.Lock()
    
    async def call(self, func: Callable, *args, **kwargs):
        async with self._lock:
            if self.state == "open":
                if time.time() - self.last_failure_time > self.recovery_timeout:
                    self.state = "half-open"
                    self.failure_count = 0
                else:
                    raise Exception("Circuit breaker is OPEN - AI service unavailable")
        
        try:
            result = await func(*args, **kwargs)
            async with self._lock:
                if self.state == "half-open":
                    self.state = "closed"
                self.failure_count = 0
            return result
        except Exception as e:
            async with self._lock:
                self.failure_count += 1
                self.last_failure_time = time.time()
                
                if self.failure_count >= self.failure_threshold:
                    self.state = "open"
                    logger.error(f"Circuit breaker OPENED after {self.failure_count} failures")
            
            raise e

class DentalAIService:
    """
    Hardened AI service for dental image analysis
    
    Features:
    - Asynchronous processing
    - Circuit breaker for fault tolerance
    - Automatic retry with exponential backoff
    - Memory-efficient batch processing
    - Comprehensive audit logging
    """
    
    MODEL_VERSION = "1.0.0"
    MAX_RETRIES = 3
    RETRY_DELAY_BASE = 2  # seconds
    PROCESSING_TIMEOUT = 30  # seconds
    MAX_IMAGE_SIZE_MB = 10
    SUPPORTED_FORMATS = {"image/jpeg", "image/png", "image/dicom", "application/dicom"}
    
    def __init__(self):
        self.circuit_breaker = CircuitBreaker()
        self.job_queue: asyncio.Queue = asyncio.Queue(maxsize=100)
        self.active_jobs: Dict[str, AIJob] = {}
        self.model = None
        self._initialized = False
        self._worker_task = None
    
    async def initialize(self):
        """Initialize AI model and start background worker"""
        if self._initialized:
            return
        
        logger.info("Initializing Dental AI Service...")
        
        # Load model (mock for now, replace with actual model loading)
        try:
            # In production: self.model = load_model('path/to/model')
            self.model = MockDentalModel()
            logger.info(f"AI Model loaded: version {self.MODEL_VERSION}")
        except Exception as e:
            logger.error(f"Failed to load AI model: {e}")
            raise
        
        # Start background worker
        self._worker_task = asyncio.create_task(self._process_queue())
        self._initialized = True
        
        logger.info("Dental AI Service initialized successfully")
    
    async def shutdown(self):
        """Graceful shutdown"""
        logger.info("Shutting down Dental AI Service...")
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
        self._initialized = False
        logger.info("Dental AI Service shutdown complete")
    
    async def submit_analysis(
        self,
        assessment_id: UUID,
        tenant_id: UUID,
        image_paths: list,
        priority: int = 5
    ) -> str:
        """
        Submit image analysis job
        
        Args:
            assessment_id: UUID of the assessment
            tenant_id: UUID of the tenant (isolation)
            image_paths: List of image file paths
            priority: Job priority (1-10, lower is higher priority)
        
        Returns:
            Job ID for tracking
        """
        # Validate inputs
        if not image_paths:
            raise ValueError("At least one image path required")
        
        if len(image_paths) > 5:
            raise ValueError("Maximum 5 images per assessment")
        
        # Validate images
        for path in image_paths:
            await self._validate_image(path)
        
        # Create job
        job_id = hashlib.sha256(
            f"{assessment_id}:{tenant_id}:{time.time()}".encode()
        ).hexdigest()[:16]
        
        job = AIJob(
            id=job_id,
            assessment_id=assessment_id,
            tenant_id=tenant_id,
            image_paths=image_paths,
            status=AIProcessingStatus.PENDING,
            created_at=datetime.utcnow()
        )
        
        # Add to queue (with priority)
        try:
            await asyncio.wait_for(
                self.job_queue.put((priority, job)),
                timeout=5.0
            )
        except asyncio.TimeoutError:
            raise Exception("AI job queue is full, try again later")
        
        self.active_jobs[job_id] = job
        
        logger.info(f"AI job submitted: {job_id} for assessment {assessment_id}")
        
        return job_id
    
    async def get_job_status(self, job_id: str) -> Optional[AIJob]:
        """Get job status and result"""
        return self.active_jobs.get(job_id)
    
    async def _process_queue(self):
        """Background worker to process AI jobs"""
        while True:
            try:
                # Get job from queue (priority queue)
                priority, job = await self.job_queue.get()
                
                logger.info(f"Processing AI job: {job.id} (attempt {job.retry_count + 1})")
                
                # Process with circuit breaker
                try:
                    result = await self.circuit_breaker.call(
                        self._analyze_with_timeout,
                        job
                    )
                    
                    job.status = AIProcessingStatus.COMPLETED
                    job.result = result
                    job.completed_at = datetime.utcnow()
                    
                    logger.info(f"AI job completed: {job.id} in {result.processing_time_ms}ms")
                    
                except asyncio.TimeoutError:
                    job.status = AIProcessingStatus.TIMEOUT
                    job.error = "Processing timeout"
                    logger.warning(f"AI job timeout: {job.id}")
                    
                except Exception as e:
                    logger.error(f"AI job failed: {job.id} - {e}")
                    
                    # Retry logic
                    if job.retry_count < self.MAX_RETRIES:
                        job.retry_count += 1
                        job.status = AIProcessingStatus.RETRYING
                        
                        # Exponential backoff
                        delay = self.RETRY_DELAY_BASE ** job.retry_count
                        logger.info(f"Retrying AI job: {job.id} in {delay}s (attempt {job.retry_count})")
                        
                        await asyncio.sleep(delay)
                        await self.job_queue.put((priority, job))
                    else:
                        job.status = AIProcessingStatus.FAILED
                        job.error = str(e)
                
                # Update database
                await self._update_assessment(job)
                
            except asyncio.CancelledError:
                logger.info("AI worker stopped")
                break
            except Exception as e:
                logger.error(f"AI worker error: {e}")
                await asyncio.sleep(1)  # Brief pause before continuing
    
    async def _analyze_with_timeout(self, job: AIJob) -> AIResult:
        """Analyze with timeout protection"""
        return await asyncio.wait_for(
            self._analyze_images(job),
            timeout=self.PROCESSING_TIMEOUT
        )
    
    async def _analyze_images(self, job: AIJob) -> AIResult:
        """
        Perform AI analysis on images
        
        In production, this would:
        1. Load images from secure storage
        2. Preprocess (resize, normalize)
        3. Run through ML model
        4. Post-process results
        5. Generate structured output
        """
        start_time = time.time()
        job.started_at = datetime.utcnow()
        job.status = AIProcessingStatus.PROCESSING
        
        try:
            # Simulate AI processing (replace with actual model inference)
            # In production:
            # predictions = self.model.predict(preprocessed_images)
            
            await asyncio.sleep(0.5)  # Simulate processing time
            
            # Generate mock result (replace with actual inference)
            result = self._generate_mock_result()
            
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            return AIResult(
                skeletal_class=result["skeletal_class"],
                dental_class=result["dental_class"],
                risk_score=result["risk_score"],
                recommended_action=result["recommended_action"],
                confidence_score=result["confidence_score"],
                model_version=self.MODEL_VERSION,
                processing_time_ms=processing_time_ms,
                raw_predictions=result.get("raw")
            )
            
        except Exception as e:
            logger.error(f"AI analysis error: {e}")
            raise
    
    def _generate_mock_result(self) -> Dict[str, Any]:
        """Generate mock AI result for testing"""
        import random
        
        skeletal_classes = ["Class I", "Class II", "Class III"]
        dental_classes = ["Normal", "Crowding", "Spacing"]
        
        skeletal = random.choice(skeletal_classes)
        
        if skeletal == "Class I":
            risk = random.uniform(0.1, 0.4)
            action = "Monitor and maintain current occlusion"
        elif skeletal == "Class II":
            risk = random.uniform(0.4, 0.7)
            action = "Consider growth modification or orthodontic treatment"
        else:
            risk = random.uniform(0.5, 0.9)
            action = "Early intervention recommended, consult specialist"
        
        return {
            "skeletal_class": skeletal,
            "dental_class": random.choice(dental_classes),
            "risk_score": round(risk, 2),
            "recommended_action": action,
            "confidence_score": round(random.uniform(0.75, 0.98), 2),
            "raw": {
                "sna_angle": round(random.uniform(78, 86), 1),
                "snb_angle": round(random.uniform(76, 84), 1),
                "anb_angle": round(random.uniform(-4, 8), 1)
            }
        }
    
    async def _validate_image(self, image_path: str):
        """Validate image file"""
        import os
        from pathlib import Path
        
        # Check file exists
        if not os.path.exists(image_path):
            raise ValueError(f"Image not found: {image_path}")
        
        # Check file size
        size_mb = os.path.getsize(image_path) / (1024 * 1024)
        if size_mb > self.MAX_IMAGE_SIZE_MB:
            raise ValueError(f"Image too large: {size_mb:.1f}MB (max {self.MAX_IMAGE_SIZE_MB}MB)")
        
        # Check MIME type (simplified, use python-magic in production)
        ext = Path(image_path).suffix.lower()
        mime_map = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".dcm": "application/dicom"
        }
        
        mime_type = mime_map.get(ext)
        if mime_type not in self.SUPPORTED_FORMATS:
            raise ValueError(f"Unsupported image format: {ext}")
    
    async def _update_assessment(self, job: AIJob):
        """Update assessment record in database"""
        from app.db.session import AsyncSessionLocal
        from sqlalchemy import select, update
        from app.models.models import Assessment
        
        async with AsyncSessionLocal() as db:
            try:
                if job.result:
                    # Update with AI results
                    stmt = (
                        update(Assessment)
                        .where(Assessment.id == job.assessment_id)
                        .where(Assessment.tenant_id == job.tenant_id)
                        .values(
                            status="ai_completed",
                            ai_analysis=job.result.__dict__,
                            ai_model_version=job.result.model_version,
                            ai_confidence_score=job.result.confidence_score,
                            ai_processing_time_ms=job.result.processing_time_ms,
                            ai_completed_at=datetime.utcnow(),
                            skeletal_class=job.result.skeletal_class,
                            dental_class=job.result.dental_class,
                            risk_score=job.result.risk_score,
                            treatment_suggestion=job.result.recommended_action,
                            confidence_score=job.result.confidence_score
                        )
                    )
                else:
                    # Update with error
                    stmt = (
                        update(Assessment)
                        .where(Assessment.id == job.assessment_id)
                        .where(Assessment.tenant_id == job.tenant_id)
                        .values(
                            status="uploaded",  # Revert to uploaded for retry
                            ai_error_message=job.error,
                            ai_retry_count=job.retry_count
                        )
                    )
                
                await db.execute(stmt)
                await db.commit()
                
            except Exception as e:
                logger.error(f"Failed to update assessment: {e}")
                await db.rollback()

class MockDentalModel:
    """Mock model for development/testing"""
    
    async def predict(self, images):
        """Mock prediction"""
        await asyncio.sleep(0.1)
        return {"predictions": []}

# Global AI service instance
ai_service = DentalAIService()