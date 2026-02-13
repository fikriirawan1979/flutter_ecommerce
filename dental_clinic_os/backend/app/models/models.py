import uuid
from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import Column, String, DateTime, Boolean, Float, ForeignKey, Text, Enum, JSON, Integer, event
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, declared_attr
from app.db.session import Base

# Enums
class UserRole(str, PyEnum):
    PATIENT = "patient"
    DOCTOR = "doctor"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"

class OrderStatus(str, PyEnum):
    PENDING = "pending"
    PAID = "paid"
    PROCESSING = "processing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"

class AssessmentStatus(str, PyEnum):
    PENDING_UPLOAD = "pending_upload"
    UPLOADED = "uploaded"
    AI_PROCESSING = "ai_processing"
    AI_COMPLETED = "ai_completed"
    IN_REVIEW = "in_review"
    COMPLETED = "completed"
    REJECTED = "rejected"

class TenantStatus(str, PyEnum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    TRIAL = "trial"
    CANCELLED = "cancelled"

class Tenant(Base):
    """Multi-tenant isolation root - every table must reference this"""
    __tablename__ = "tenants"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, index=True, nullable=False)
    domain = Column(String(255), unique=True, nullable=True)
    status = Column(Enum(TenantStatus), default=TenantStatus.TRIAL, nullable=False)
    
    # Stripe Connect
    stripe_account_id = Column(String(255), nullable=True)
    stripe_charges_enabled = Column(Boolean, default=False)
    stripe_payouts_enabled = Column(Boolean, default=False)
    
    # Storage isolation
    storage_bucket = Column(String(255), nullable=False, unique=True)
    storage_prefix = Column(String(50), nullable=False, unique=True)
    
    # Settings
    settings = Column(JSON, default=dict, nullable=False)
    feature_flags = Column(JSON, default=dict, nullable=False)
    
    # Billing
    plan = Column(String(50), default="basic", nullable=False)
    max_users = Column(Integer, default=10, nullable=False)
    max_storage_gb = Column(Float, default=100.0, nullable=False)
    monthly_revenue = Column(Float, default=0.0, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    trial_ends_at = Column(DateTime, nullable=True)
    
    # Relationships
    users = relationship("User", back_populates="tenant", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="tenant", cascade="all, delete-orphan")
    assessments = relationship("Assessment", back_populates="tenant", cascade="all, delete-orphan")
    products = relationship("Product", back_populates="tenant", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="tenant", cascade="all, delete-orphan")

class TenantMixin:
    """Mixin to add tenant_id to all models"""
    
    @declared_attr
    def tenant_id(cls):
        return Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    
    @declared_attr
    def tenant(cls):
        return relationship("Tenant", back_populates=cls.__tablename__)

class User(Base, TenantMixin):
    """User model with tenant isolation"""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=True)
    role = Column(Enum(UserRole), default=UserRole.PATIENT, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    avatar_url = Column(String(500), nullable=True)
    
    # Profile fields
    date_of_birth = Column(DateTime, nullable=True)
    gender = Column(String(20), nullable=True)
    address = Column(Text, nullable=True)
    
    # Security
    failed_login_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(DateTime, nullable=True)
    password_changed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_password_reset = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_login = Column(DateTime, nullable=True)
    
    # Unique constraint per tenant
    __table_args__ = (
        # Email must be unique within tenant
        # This is handled at application level due to SQLAlchemy limitations
    )
    
    # Relationships
    orders = relationship("Order", back_populates="patient", foreign_keys="Order.patient_id")
    assessments_as_doctor = relationship("Assessment", back_populates="doctor", foreign_keys="Assessment.doctor_id")
    assessments_as_patient = relationship("Assessment", back_populates="patient", foreign_keys="Assessment.patient_id")
    audit_logs = relationship("AuditLog", back_populates="user", foreign_keys="AuditLog.user_id")

class Product(Base, TenantMixin):
    """Product/Package model with tenant isolation"""
    __tablename__ = "products"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    price = Column(Float, nullable=False)
    stripe_price_id = Column(String(255), nullable=True)
    image_url = Column(String(500), nullable=True)
    features = Column(JSON, default=list)
    is_active = Column(Boolean, default=True, nullable=False)
    sort_order = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    order_items = relationship("OrderItem", back_populates="product")

class Order(Base, TenantMixin):
    """Order model with tenant isolation"""
    __tablename__ = "orders"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    total_amount = Column(Float, nullable=False)
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING, nullable=False)
    
    # Stripe
    stripe_payment_intent_id = Column(String(255), nullable=True, index=True)
    stripe_charge_id = Column(String(255), nullable=True)
    stripe_receipt_url = Column(String(500), nullable=True)
    
    # Payment tracking
    payment_method = Column(String(50), nullable=True)
    idempotency_key = Column(String(255), unique=True, nullable=True, index=True)
    
    # Invoice
    invoice_number = Column(String(50), nullable=False, unique=True)
    invoice_pdf_url = Column(String(500), nullable=True)
    
    # Refund tracking
    refunded_amount = Column(Float, default=0.0, nullable=False)
    refund_reason = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    paid_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    patient = relationship("User", back_populates="orders", foreign_keys=[patient_id])
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    assessment = relationship("Assessment", back_populates="order", uselist=False)

class OrderItem(Base, TenantMixin):
    """Order item model"""
    __tablename__ = "order_items"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, default=1, nullable=False)
    unit_price = Column(Float, nullable=False)
    total_price = Column(Float, nullable=False)
    
    # Relationships
    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")

class Assessment(Base, TenantMixin):
    """Assessment model with full AI tracking"""
    __tablename__ = "assessments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=False)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    doctor_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Status
    status = Column(Enum(AssessmentStatus), default=AssessmentStatus.PENDING_UPLOAD, nullable=False)
    
    # Cephalometric measurements
    sna = Column(Float, nullable=True)
    snb = Column(Float, nullable=True)
    anb = Column(Float, nullable=True)
    overjet = Column(Float, nullable=True)
    overbite = Column(Float, nullable=True)
    additional_measurements = Column(JSON, default=dict)
    
    # AI Analysis Results
    ai_analysis = Column(JSON, nullable=True)
    ai_model_version = Column(String(50), nullable=True)
    ai_confidence_score = Column(Float, nullable=True)
    ai_processing_time_ms = Column(Integer, nullable=True)
    ai_error_message = Column(Text, nullable=True)
    ai_retry_count = Column(Integer, default=0, nullable=False)
    
    # Final Assessment (Doctor + AI combined)
    skeletal_class = Column(String(50), nullable=True)
    dental_class = Column(String(50), nullable=True)
    severity = Column(String(50), nullable=True)
    risk_score = Column(Float, nullable=True)
    treatment_suggestion = Column(Text, nullable=True)
    recommended_action = Column(Text, nullable=True)
    confidence_score = Column(Float, nullable=True)
    diagnosis_notes = Column(Text, nullable=True)
    
    # Report
    report_pdf_url = Column(String(500), nullable=True)
    generated_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    ai_started_at = Column(DateTime, nullable=True)
    ai_completed_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    order = relationship("Order", back_populates="assessment")
    patient = relationship("User", back_populates="assessments_as_patient", foreign_keys=[patient_id])
    doctor = relationship("User", back_populates="assessments_as_doctor", foreign_keys=[doctor_id])
    images = relationship("AssessmentImage", back_populates="assessment", cascade="all, delete-orphan")

class AssessmentImage(Base, TenantMixin):
    """Image upload with strict validation"""
    __tablename__ = "assessment_images"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    assessment_id = Column(UUID(as_uuid=True), ForeignKey("assessments.id"), nullable=False)
    
    # File info
    file_url = Column(String(500), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_type = Column(Enum("xray", "intraoral", "cephalometric", "panoramic", name="image_type"), nullable=False)
    mime_type = Column(String(100), nullable=False)
    file_size = Column(Integer, nullable=False)
    checksum_sha256 = Column(String(64), nullable=False, index=True)
    
    # Storage isolation
    storage_path = Column(String(500), nullable=False)
    
    # Validation
    validated = Column(Boolean, default=False, nullable=False)
    validation_error = Column(Text, nullable=True)
    
    # Annotations (for doctor review)
    annotations = Column(JSON, default=list)
    
    # Timestamps
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    processed_at = Column(DateTime, nullable=True)
    
    # Relationships
    assessment = relationship("Assessment", back_populates="images")

class AuditLog(Base):
    """Comprehensive audit logging for compliance"""
    __tablename__ = "audit_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    
    # Event details
    action = Column(String(100), nullable=False, index=True)
    resource_type = Column(String(50), nullable=False)  # user, order, assessment, etc.
    resource_id = Column(UUID(as_uuid=True), nullable=True)
    
    # Request context
    ip_address = Column(String(45), nullable=True)  # IPv6 compatible
    user_agent = Column(Text, nullable=True)
    request_id = Column(String(100), nullable=True, index=True)
    
    # Changes (for update operations)
    before_data = Column(JSON, nullable=True)
    after_data = Column(JSON, nullable=True)
    
    # Status
    success = Column(Boolean, nullable=False)
    error_message = Column(Text, nullable=True)
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="audit_logs")
    user = relationship("User", back_populates="audit_logs", foreign_keys=[user_id])

# Indexes for performance
from sqlalchemy import Index

# Composite indexes for common queries
Index('idx_orders_tenant_status', Order.tenant_id, Order.status)
Index('idx_orders_tenant_patient', Order.tenant_id, Order.patient_id)
Index('idx_assessments_tenant_status', Assessment.tenant_id, Assessment.status)
Index('idx_assessments_tenant_patient', Assessment.tenant_id, Assessment.patient_id)
Index('idx_audit_logs_tenant_created', AuditLog.tenant_id, AuditLog.created_at)
Index('idx_users_tenant_email', User.tenant_id, User.email)