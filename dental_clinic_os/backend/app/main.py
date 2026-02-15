from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
import logging
import time

from app.core.config import settings
from app.db.session import init_db
from app.api.v1.endpoints import auth, assessments, products, orders, users, stripe_webhooks, tenants, ai_analysis
from app.middleware.tenant_middleware import TenantMiddleware, AuditMiddleware, RateLimitMiddleware
from app.core.i18n import LocaleMiddleware

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    # Startup
    logger.info("Starting up DentalClinicOS API...")
    try:
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down DentalClinicOS API...")

app = FastAPI(
    title=settings.APP_NAME,
    description="""
    DentalClinicOS API - A comprehensive dental assessment clinic management system.
    
    ## Features
    
    * **Authentication**: JWT-based authentication with role-based access control
    * **E-commerce**: Assessment package ordering system
    * **File Upload**: Secure image upload for X-rays and intraoral photos
    * **Assessment Engine**: Rule-based cephalometric analysis
    * **Reporting**: PDF report generation
    
    ## Roles
    
    * **Patient**: Can order assessments, upload images, view reports
    * **Doctor**: Can review assessments, perform analysis, generate reports
    * **Admin**: Full system management, analytics, user management
    """,
    version=settings.VERSION,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security and audit middleware
app.add_middleware(AuditMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(TenantMiddleware)
app.add_middleware(LocaleMiddleware)

# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation error",
            "errors": exc.errors()
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "message": str(exc) if settings.DEBUG else "An unexpected error occurred"
        }
    )

# Include routers
app.include_router(
    auth.router,
    prefix="/api/v1"
)
app.include_router(
    assessments.router,
    prefix="/api/v1"
)
app.include_router(
    products.router,
    prefix="/api/v1"
)
app.include_router(
    orders.router,
    prefix="/api/v1"
)
app.include_router(
    users.router,
    prefix="/api/v1"
)
app.include_router(
    stripe_webhooks.router,
    prefix="/api/v1"
)
app.include_router(
    tenants.router,
    prefix="/api/v1"
)
app.include_router(
    ai_analysis.router,
    prefix="/api/v1"
)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to DentalClinicOS API",
        "version": settings.VERSION,
        "docs": "/api/docs",
        "health": "/api/health"
    }

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )