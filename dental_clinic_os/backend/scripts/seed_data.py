"""
Database seeding script for initial setup
Creates demo tenant and sample data
"""

import asyncio
import sys
from uuid import uuid4
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.append("/home/engine/project/dental_clinic_os/backend")

from app.db.session import async_engine, AsyncSessionLocal
from app.core.security import get_password_hash
from app.models.models import (
    Base, Tenant, User, UserRole, TenantStatus,
    Product, Order, OrderStatus, Assessment, AssessmentStatus
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select


async def create_demo_tenant(db: AsyncSession) -> Tenant:
    """Create a demo tenant"""
    tenant = Tenant(
        id=uuid4(),
        name="Demo Dental Clinic",
        slug="demo-clinic",
        domain="demo.dentalclinic.com",
        status=TenantStatus.ACTIVE,
        storage_bucket="demo-clinic-uploads",
        storage_prefix="demo",
        plan="professional",
        max_users=50,
        max_storage_gb=500.0,
        settings={
            "clinic_name": "Demo Dental Clinic",
            "address": "123 Main St, City",
            "phone": "+1234567890",
            "email": "contact@democlinic.com"
        },
        feature_flags={
            "ai_analysis": True,
            "stripe_payments": True,
            "pdf_reports": True
        },
        trial_ends_at=datetime.utcnow() + timedelta(days=30)
    )
    
    db.add(tenant)
    await db.commit()
    await db.refresh(tenant)
    
    print(f"Created tenant: {tenant.name} (ID: {tenant.id})")
    return tenant


async def create_demo_users(db: AsyncSession, tenant_id: uuid4) -> dict:
    """Create demo users for the tenant"""
    users = {}
    
    demo_users_data = [
        {
            "email": "admin@demo.com",
            "password": "Admin123!",
            "first_name": "Admin",
            "last_name": "User",
            "role": UserRole.ADMIN
        },
        {
            "email": "doctor@demo.com",
            "password": "Doctor123!",
            "first_name": "Doctor",
            "last_name": "Smith",
            "role": UserRole.DOCTOR
        },
        {
            "email": "patient@demo.com",
            "password": "Patient123!",
            "first_name": "John",
            "last_name": "Doe",
            "role": UserRole.PATIENT
        }
    ]
    
    for user_data in demo_users_data:
        user = User(
            id=uuid4(),
            email=user_data["email"],
            hashed_password=get_password_hash(user_data["password"]),
            first_name=user_data["first_name"],
            last_name=user_data["last_name"],
            role=user_data["role"],
            tenant_id=tenant_id,
            is_active=True,
            is_verified=True
        )
        db.add(user)
        users[user_data["role"].value] = user
        print(f"Created user: {user.email} ({user.role.value})")
    
    await db.commit()
    return users


async def create_demo_products(db: AsyncSession, tenant_id: uuid4) -> list:
    """Create demo products"""
    products = []
    
    demo_products = [
        {
            "name": "Basic Assessment",
            "description": "Standard dental assessment with X-ray analysis",
            "price": 149.99,
            "features": ["X-ray Analysis", "Digital Report", "Treatment Suggestions"]
        },
        {
            "name": "Comprehensive Assessment",
            "description": "Complete dental assessment including AI analysis",
            "price": 299.99,
            "features": ["AI-Powered Analysis", "Cephalometric Measurements", "Priority Support", "Video Consultation"]
        },
        {
            "name": "Premium Package",
            "description": "Full assessment with treatment planning",
            "price": 499.99,
            "features": ["Everything in Comprehensive", "3D Treatment Plan", "Follow-up Consultation", "1 Year Support"]
        }
    ]
    
    for i, product_data in enumerate(demo_products):
        product = Product(
            id=uuid4(),
            tenant_id=tenant_id,
            name=product_data["name"],
            description=product_data["description"],
            price=product_data["price"],
            features=product_data["features"],
            is_active=True,
            sort_order=i
        )
        db.add(product)
        products.append(product)
        print(f"Created product: {product.name} (${product.price})")
    
    await db.commit()
    return products


async def seed_database():
    """Main seeding function"""
    print("=" * 60)
    print("DentalClinicOS Database Seeding")
    print("=" * 60)
    
    # Create tables
    print("\n1. Creating database tables...")
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("   Tables created successfully!")
    
    async with AsyncSessionLocal() as db:
        # Check if already seeded
        result = await db.execute(select(Tenant))
        existing = result.scalar_one_or_none()
        
        if existing:
            print("\nDatabase already seeded!")
            print(f"Tenant: {existing.name} (ID: {existing.id})")
            return
        
        # Create tenant
        print("\n2. Creating demo tenant...")
        tenant = await create_demo_tenant(db)
        
        # Create users
        print("\n3. Creating demo users...")
        users = await create_demo_users(db, tenant.id)
        
        # Create products
        print("\n4. Creating demo products...")
        products = await create_demo_products(db, tenant.id)
        
        print("\n" + "=" * 60)
        print("Seeding completed successfully!")
        print("=" * 60)
        print(f"\nTenant ID: {tenant.id}")
        print(f"Use this ID in the X-Tenant-ID header for API requests")
        print("\nDemo Login Credentials:")
        print("  Admin:    admin@demo.com / Admin123!")
        print("  Doctor:   doctor@demo.com / Doctor123!")
        print("  Patient:  patient@demo.com / Patient123!")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(seed_database())
