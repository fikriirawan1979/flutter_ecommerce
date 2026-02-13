"""
Tenant Isolation Middleware
Ensures complete data isolation between tenants
"""

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from sqlalchemy import select
from typing import Optional
import logging

from app.db.session import AsyncSessionLocal
from app.models.models import Tenant, TenantStatus, User
from app.core.security import rate_limiter

logger = logging.getLogger(__name__)

# Context variable to store current tenant
from contextvars import ContextVar

tenant_context: ContextVar[Optional[Tenant]] = ContextVar('tenant', default=None)
current_user_context: ContextVar[Optional[User]] = ContextVar('current_user', default=None)

def get_current_tenant() -> Optional[Tenant]:
    """Get current tenant from context"""
    return tenant_context.get()

def get_current_user_from_context() -> Optional[User]:
    """Get current user from context"""
    return current_user_context.get()

class TenantMiddleware(BaseHTTPMiddleware):
    """
    Middleware to extract and validate tenant from request
    Supports subdomain and header-based tenant identification
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next):
        # Skip tenant check for public endpoints
        public_paths = [
            "/api/v1/auth/login",
            "/api/v1/auth/register",
            "/api/v1/auth/refresh",
            "/api/health",
            "/api/docs",
            "/api/redoc",
            "/api/openapi.json"
        ]
        
        if any(request.url.path.startswith(path) for path in public_paths):
            response = await call_next(request)
            return response
        
        # Extract tenant identifier
        tenant_slug = None
        
        # 1. Check subdomain (e.g., clinic1.dentalclinicos.com)
        host = request.headers.get("host", "")
        if "." in host:
            subdomain = host.split(".")[0]
            if subdomain not in ["www", "api", "app"]:
                tenant_slug = subdomain
        
        # 2. Check X-Tenant-ID header
        if not tenant_slug:
            tenant_slug = request.headers.get("x-tenant-id")
        
        # 3. Check JWT token for tenant_id
        if not tenant_slug:
            auth_header = request.headers.get("authorization", "")
            if auth_header.startswith("Bearer "):
                token = auth_header[7:]
                from app.core.security import decode_token
                payload = decode_token(token)
                if payload and "tenant_id" in payload:
                    tenant_slug = payload["tenant_id"]
        
        if not tenant_slug:
            logger.warning(f"No tenant identifier found for request: {request.url.path}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tenant identifier required (subdomain, X-Tenant-ID header, or JWT token)"
            )
        
        # Validate tenant
        async with AsyncSessionLocal() as db:
            # Check if it's a UUID or slug
            from uuid import UUID
            try:
                tenant_id = UUID(tenant_slug)
                result = await db.execute(
                    select(Tenant).where(Tenant.id == tenant_id)
                )
            except ValueError:
                # It's a slug
                result = await db.execute(
                    select(Tenant).where(Tenant.slug == tenant_slug)
                )
            
            tenant = result.scalar_one_or_none()
            
            if not tenant:
                logger.warning(f"Tenant not found: {tenant_slug}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Tenant not found"
                )
            
            if tenant.status == TenantStatus.SUSPENDED:
                logger.warning(f"Suspended tenant attempted access: {tenant_slug}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Tenant account suspended"
                )
            
            if tenant.status == TenantStatus.CANCELLED:
                logger.warning(f"Cancelled tenant attempted access: {tenant_slug}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Tenant account cancelled"
                )
            
            if tenant.status == TenantStatus.TRIAL and tenant.trial_ends_at:
                from datetime import datetime
                if datetime.utcnow() > tenant.trial_ends_at:
                    logger.warning(f"Expired trial tenant: {tenant_slug}")
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Trial period expired"
                    )
            
            # Store tenant in context
            tenant_token = tenant_context.set(tenant)
            request.state.tenant = tenant
            
            try:
                response = await call_next(request)
                
                # Add tenant headers for debugging (remove in production)
                response.headers["X-Tenant-ID"] = str(tenant.id)
                
                return response
            finally:
                tenant_context.reset(tenant_token)

class AuditMiddleware(BaseHTTPMiddleware):
    """Audit logging middleware"""
    
    async def dispatch(self, request: Request, call_next):
        from uuid import uuid4
        
        # Generate request ID
        request_id = str(uuid4())
        request.state.request_id = request_id
        
        # Get client IP
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        else:
            client_ip = request.client.host if request.client else "unknown"
        
        request.state.client_ip = client_ip
        
        # Process request
        start_time = __import__('time').time()
        
        try:
            response = await call_next(request)
            
            # Log successful request
            duration = __import__('time').time() - start_time
            logger.info(
                f"Request: {request.method} {request.url.path} - "
                f"Status: {response.status_code} - "
                f"Duration: {duration:.3f}s - "
                f"IP: {client_ip} - "
                f"RequestID: {request_id}"
            )
            
            # Add security headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["X-XSS-Protection"] = "1; mode=block"
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
            
            return response
            
        except Exception as e:
            # Log failed request
            duration = __import__('time').time() - start_time
            logger.error(
                f"Request Failed: {request.method} {request.url.path} - "
                f"Error: {str(e)} - "
                f"Duration: {duration:.3f}s - "
                f"IP: {client_ip} - "
                f"RequestID: {request_id}"
            )
            raise

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks
        if request.url.path in ["/api/health", "/api/health/"]:
            return await call_next(request)
        
        # Get client identifier
        client_ip = request.client.host if request.client else "unknown"
        tenant = getattr(request.state, 'tenant', None)
        
        # Create rate limit key
        if tenant:
            key = f"{tenant.id}:{client_ip}:{request.url.path}"
            max_requests = 100  # Per tenant per IP
        else:
            key = f"global:{client_ip}"
            max_requests = 30  # Stricter for unauthenticated
        
        # Check rate limit
        if not rate_limiter.is_allowed(key, max_requests=max_requests, window_seconds=60):
            logger.warning(f"Rate limit exceeded for {key}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again later."
            )
        
        return await call_next(request)

def require_tenant():
    """Dependency to ensure tenant context is set"""
    tenant = get_current_tenant()
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant context not available"
        )
    return tenant

def tenant_scoped_query(model_class):
    """Decorator/wrapper to automatically scope queries by tenant"""
    def wrapper(query_func):
        async def wrapped(*args, **kwargs):
            tenant = get_current_tenant()
            if tenant and hasattr(model_class, 'tenant_id'):
                # Automatically add tenant filter
                from sqlalchemy import select
                query = select(model_class).where(model_class.tenant_id == tenant.id)
                kwargs['tenant_scoped_query'] = query
            return await query_func(*args, **kwargs)
        return wrapped
    return wrapper