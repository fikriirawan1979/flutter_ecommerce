"""
MinIO Object Storage Service
Handles file uploads with tenant isolation and validation
"""

import os
import hashlib
import mimetypes
from typing import Optional, Dict, Any
from pathlib import Path
from datetime import datetime
import logging

try:
    from minio import Minio
    from minio.error import S3Error
    MINIO_AVAILABLE = True
except ImportError:
    MINIO_AVAILABLE = False
    Minio = None

from app.core.config import settings
from app.middleware.tenant_middleware import get_current_tenant

logger = logging.getLogger(__name__)


class MinIOService:
    """
    MinIO service for file storage with multi-tenant isolation
    """
    
    def __init__(self):
        if not MINIO_AVAILABLE:
            logger.warning("MinIO client not available. Install with: pip install minio")
            return
        
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize MinIO client"""
        try:
            self.client = Minio(
                f"{settings.MINIO_ENDPOINT}",
                access_key=settings.MINIO_ACCESS_KEY,
                secret_key=settings.MINIO_SECRET_KEY,
                secure=settings.MINIO_SECURE
            )
            logger.info(f"MinIO client initialized: {settings.MINIO_ENDPOINT}")
        except Exception as e:
            logger.error(f"Failed to initialize MinIO client: {e}")
            self.client = None
    
    def _ensure_bucket(self, bucket_name: str):
        """Ensure bucket exists, create if not"""
        if not self.client:
            return False
        
        try:
            if not self.client.bucket_exists(bucket_name):
                self.client.make_bucket(bucket_name)
                logger.info(f"Created bucket: {bucket_name}")
            return True
        except S3Error as e:
            logger.error(f"Bucket operation failed: {e}")
            return False
    
    def _get_storage_path(self, tenant_id: str, assessment_id: str, filename: str) -> str:
        """Generate storage path with tenant isolation"""
        # Format: tenant_id/assessment_id/timestamp/filename
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        return f"{tenant_id}/{assessment_id}/{timestamp}/{filename}"
    
    def _calculate_checksum(self, file_content: bytes) -> str:
        """Calculate SHA-256 checksum"""
        return hashlib.sha256(file_content).hexdigest()
    
    def _validate_file(self, filename: str, file_size: int, file_content: bytes) -> tuple[bool, Optional[str]]:
        """
        Validate file
        
        Returns:
            (is_valid, error_message)
        """
        # Check file size
        if file_size > settings.UPLOAD_MAX_SIZE:
            return False, f"File too large (max {settings.UPLOAD_MAX_SIZE} bytes)"
        
        # Check file extension
        file_ext = Path(filename).suffix.lower()
        if file_ext not in settings.UPLOAD_ALLOWED_EXTENSIONS:
            return False, f"File type not allowed. Allowed: {', '.join(settings.UPLOAD_ALLOWED_EXTENSIONS)}"
        
        # Check MIME type
        mime_type, _ = mimetypes.guess_type(filename)
        if not mime_type or not mime_type.startswith(("image/", "application/dicom")):
            return False, "Invalid file type. Only images and DICOM files are allowed."
        
        return True, None
    
    async def upload_file(
        self,
        file_content: bytes,
        filename: str,
        assessment_id: str,
        image_type: str = "xray",
        tenant_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Upload file to MinIO
        
        Args:
            file_content: File content as bytes
            filename: Original filename
            assessment_id: Assessment ID for organization
            image_type: Type of image (xray, intraoral, etc.)
            tenant_id: Tenant ID (if not provided, uses current tenant from context)
            
        Returns:
            Dictionary with upload results
        """
        if not self.client:
            # Fallback: return mock URL if MinIO not available
            logger.warning("MinIO client not available, returning mock URL")
            return {
                "success": False,
                "file_url": f"mock://storage/{assessment_id}/{filename}",
                "message": "MinIO not configured"
            }
        
        # Get tenant ID
        if not tenant_id:
            tenant = get_current_tenant()
            if not tenant:
                return {
                    "success": False,
                    "error": "No tenant context available"
                }
            tenant_id = str(tenant.id)
        
        # Validate file
        file_size = len(file_content)
        is_valid, error_message = self._validate_file(filename, file_size, file_content)
        if not is_valid:
            return {
                "success": False,
                "error": error_message
            }
        
        # Calculate checksum
        checksum = self._calculate_checksum(file_content)
        
        # Generate storage path
        storage_path = self._get_storage_path(tenant_id, assessment_id, filename)
        
        # Determine bucket (use tenant-specific bucket or default)
        bucket_name = settings.MINIO_BUCKET
        
        # Ensure bucket exists
        if not self._ensure_bucket(bucket_name):
            return {
                "success": False,
                "error": "Failed to access storage bucket"
            }
        
        try:
            # Upload file
            from io import BytesIO
            
            self.client.put_object(
                bucket_name,
                storage_path,
                BytesIO(file_content),
                length=file_size,
                content_type=mimetypes.guess_type(filename)[0]
            )
            
            # Generate public URL
            file_url = f"{self._get_base_url()}/{bucket_name}/{storage_path}"
            
            logger.info(f"File uploaded: {storage_path} ({file_size} bytes)")
            
            return {
                "success": True,
                "file_url": file_url,
                "storage_path": storage_path,
                "bucket_name": bucket_name,
                "file_size": file_size,
                "checksum": checksum
            }
            
        except S3Error as e:
            logger.error(f"MinIO upload failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def delete_file(self, storage_path: str, bucket_name: Optional[str] = None) -> bool:
        """
        Delete file from MinIO
        
        Args:
            storage_path: Path to file in bucket
            bucket_name: Bucket name (uses default if not provided)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.client:
            return False
        
        bucket_name = bucket_name or settings.MINIO_BUCKET
        
        try:
            self.client.remove_object(bucket_name, storage_path)
            logger.info(f"File deleted: {storage_path}")
            return True
        except S3Error as e:
            logger.error(f"Failed to delete file {storage_path}: {e}")
            return False
    
    def get_presigned_url(
        self,
        storage_path: str,
        expires: int = 3600,
        bucket_name: Optional[str] = None
    ) -> Optional[str]:
        """
        Generate presigned URL for file access
        
        Args:
            storage_path: Path to file in bucket
            expires: URL expiration time in seconds (default 1 hour)
            bucket_name: Bucket name (uses default if not provided)
            
        Returns:
            Presigned URL or None if failed
        """
        if not self.client:
            return None
        
        bucket_name = bucket_name or settings.MINIO_BUCKET
        
        try:
            url = self.client.presigned_get_object(
                bucket_name,
                storage_path,
                expires=timedelta(seconds=expires)
            )
            return url
        except S3Error as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            return None
    
    def _get_base_url(self) -> str:
        """Get base URL for MinIO"""
        if settings.MINIO_SECURE:
            return f"https://{settings.MINIO_ENDPOINT}"
        else:
            return f"http://{settings.MINIO_ENDPOINT}"
    
    async def list_files(
        self,
        tenant_id: str,
        prefix: Optional[str] = None,
        bucket_name: Optional[str] = None
    ) -> list:
        """
        List files for a tenant
        
        Args:
            tenant_id: Tenant ID to filter files
            prefix: Additional prefix filter
            bucket_name: Bucket name (uses default if not provided)
            
        Returns:
            List of file metadata
        """
        if not self.client:
            return []
        
        bucket_name = bucket_name or settings.MINIO_BUCKET
        
        try:
            search_prefix = f"{tenant_id}/"
            if prefix:
                search_prefix += prefix
            
            objects = self.client.list_objects(bucket_name, prefix=search_prefix, recursive=True)
            
            files = []
            for obj in objects:
                files.append({
                    "name": obj.object_name,
                    "size": obj.size,
                    "last_modified": obj.last_modified,
                    "etag": obj.etag
                })
            
            return files
            
        except S3Error as e:
            logger.error(f"Failed to list files: {e}")
            return []


# Global instance
minio_service = MinIOService()


async def upload_assessment_image(
    file_content: bytes,
    filename: str,
    assessment_id: str,
    image_type: str = "xray",
    tenant_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Convenience function to upload assessment image
    
    Args:
        file_content: File content as bytes
        filename: Original filename
        assessment_id: Assessment ID
        image_type: Type of image
        tenant_id: Tenant ID
        
    Returns:
        Dictionary with upload results
    """
    return await minio_service.upload_file(
        file_content,
        filename,
        assessment_id,
        image_type,
        tenant_id
    )
