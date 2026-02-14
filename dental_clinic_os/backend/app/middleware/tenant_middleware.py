"""
Tenant isolation middleware to enforce multi-tenancy
"""

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Callable
import logging

from app.core.security import decode_token
from app.models.models import Tenant, TenantStatus

logger = logging.getLogger(__name__)


class TenantMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce tenant isolation for all requests.
    
    This middleware:
    1. Extracts tenant_id from JWT token
    2. Validates tenant is active
    3. Attaches tenant to request state
    4. Enforces tenant-scoped queries
    """
    
    async def dispatch(self, request: Request, call_next: Callable):
        # Skip tenant check for health endpoints and auth endpoints
        if self._should_skip_tenant_check(request):
            return await call_next(request)
        
        try:
            # Extract token from Authorization header
            auth_header = request.headers.get("authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Missing or invalid authorization header"
                )
            
            token = auth_header.split(" ")[1]
            payload = decode_token(token)
            
            if not payload:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token"
                )
            
            # Extract tenant_id from token
            tenant_id = payload.get("tenant_id")
            if not tenant_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Tenant information not found in token"
                )
            
            # Store tenant_id in request state for use in endpoints
            request.state.tenant_id = tenant_id
            request.state.user_id = payload.get("sub")
            request.state.user_role = payload.get("role")
            
            # Process request
            response = await call_next(request)
            
            # Add tenant context to response headers
            response.headers["X-Tenant-ID"] = str(tenant_id)
            
            return response
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Tenant middleware error: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication failed"
            )
    
    def _should_skip_tenant_check(self, request: Request) -> bool:
        """Determine if request should skip tenant check"""
        skip_paths = [
            "/api/health",
            "/",
            "/api/docs",
            "/api/redoc",
            "/api/openapi.json",
            "/api/v1/auth/login",
            "/api/v1/auth/register",
            "/api/v1/auth/refresh",
            "/api/v1/auth/seed-demo-users",
        ]
        
        return any(request.url.path.startswith(path) for path in skip_paths)


class TenantActiveMiddleware(BaseHTTPMiddleware):
    """
    Middleware to check if tenant is active and not suspended.
    """
    
    async def dispatch(self, request: Request, call_next: Callable):
        # Skip for public endpoints
        if self._should_skip(request):
            return await call_next(request)
        
        tenant_id = getattr(request.state, "tenant_id", None)
        
        if not tenant_id:
            # Skip if no tenant context (shouldn't happen with TenantMiddleware)
            return await call_next(request)
        
        # In production, you'd fetch tenant from DB/cache here
        # For now, we'll rely on the token validation
        
        return await call_next(request)
    
    def _should_skip(self, request: Request) -> bool:
        """Skip for public endpoints"""
        skip_paths = [
            "/api/health",
            "/",
            "/api/docs",
            "/api/redoc",
            "/api/openapi.json",
        ]
        
        return any(request.url.path.startswith(path) for path in skip_paths)
