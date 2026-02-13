from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from app.models.models import UserRole, OrderStatus, AssessmentStatus

# Base schemas
class UserBase(BaseModel):
    email: EmailStr
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    phone: Optional[str] = None
    role: UserRole = UserRole.PATIENT

class UserCreate(UserBase):
    password: str = Field(..., min_length=6)

class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None

class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    is_active: bool
    avatar_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class UserProfile(UserResponse):
    date_of_birth: Optional[datetime] = None
    gender: Optional[str] = None
    address: Optional[str] = None

# Auth schemas
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_at: datetime

class TokenPayload(BaseModel):
    sub: Optional[str] = None
    type: Optional[str] = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class RefreshRequest(BaseModel):
    refresh_token: str

# Product schemas
class ProductBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str
    price: float = Field(..., gt=0)
    features: List[str] = []

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    features: Optional[List[str]] = None
    is_active: Optional[bool] = None

class ProductResponse(ProductBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    image_url: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

# Order schemas
class OrderItemCreate(BaseModel):
    product_id: UUID
    quantity: int = Field(..., ge=1)

class OrderCreate(BaseModel):
    items: List[OrderItemCreate]

class OrderItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    product: ProductResponse
    quantity: int
    unit_price: float
    total_price: float

class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    patient_id: UUID
    total_amount: float
    status: OrderStatus
    invoice_number: str
    items: List[OrderItemResponse]
    created_at: datetime
    updated_at: datetime
    paid_at: Optional[datetime] = None

# Assessment schemas
class CephalometricMeasurements(BaseModel):
    sna: Optional[float] = None
    snb: Optional[float] = None
    anb: Optional[float] = None
    overjet: Optional[float] = None
    overbite: Optional[float] = None

class AssessmentCreate(BaseModel):
    order_id: UUID

class AssessmentUpdate(BaseModel):
    measurements: Optional[CephalometricMeasurements] = None
    additional_measurements: Optional[dict] = None
    diagnosis_notes: Optional[str] = None

class AssessmentResult(BaseModel):
    skeletal_class: str
    severity: str
    treatment_suggestion: str
    confidence_score: float

class AssessmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    order_id: UUID
    patient_id: UUID
    doctor_id: Optional[UUID] = None
    status: AssessmentStatus
    measurements: Optional[CephalometricMeasurements] = None
    additional_measurements: Optional[dict] = None
    skeletal_class: Optional[str] = None
    severity: Optional[str] = None
    treatment_suggestion: Optional[str] = None
    confidence_score: Optional[float] = None
    diagnosis_notes: Optional[str] = None
    report_pdf_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None

# Image upload schema
class ImageUploadResponse(BaseModel):
    id: UUID
    file_url: str
    file_name: str
    file_type: str
    uploaded_at: datetime

# Annotation schema
class Annotation(BaseModel):
    x: float
    y: float
    type: str  # circle, arrow, text
    text: Optional[str] = None
    color: str = "#FF0000"

# Dashboard stats
class DashboardStats(BaseModel):
    total_revenue: float
    total_orders: int
    total_assessments: int
    pending_reviews: int
    monthly_growth: float

# Error response
class ErrorResponse(BaseModel):
    detail: str
    error_code: Optional[str] = None