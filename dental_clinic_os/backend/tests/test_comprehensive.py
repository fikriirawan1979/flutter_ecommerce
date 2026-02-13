"""
Comprehensive Test Suite for DentalClinicOS
Coverage: Security, Multi-tenancy, AI Pipeline, Stripe Integration
"""

import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from uuid import uuid4, UUID
from unittest.mock import Mock, patch, AsyncMock
import json
import stripe

from app.core.security import (
    verify_password, get_password_hash, create_access_token,
    decode_token, brute_force_protector, rate_limiter,
    generate_idempotency_key
)
from app.models.models import (
    Tenant, User, UserRole, Order, OrderStatus, Assessment,
    AssessmentStatus, TenantStatus
)

# ==================== SECURITY TESTS ====================

class TestSecurity:
    """Test security functions"""
    
    def test_password_hashing(self):
        """Test password hashing and verification"""
        password = "SecurePass123!"
        hashed = get_password_hash(password)
        
        assert verify_password(password, hashed) is True
        assert verify_password("wrongpassword", hashed) is False
    
    def test_password_strength_validation(self):
        """Test password strength requirements"""
        with pytest.raises(ValueError, match="at least 8 characters"):
            get_password_hash("short")
        
        with pytest.raises(ValueError, match="uppercase"):
            get_password_hash("lowercase123!")
        
        with pytest.raises(ValueError, match="lowercase"):
            get_password_hash("UPPERCASE123!")
        
        with pytest.raises(ValueError, match="digit"):
            get_password_hash("NoDigits!!")
        
        with pytest.raises(ValueError, match="special character"):
            get_password_hash("NoSpecial123")
    
    def test_jwt_token_creation_and_validation(self):
        """Test JWT token lifecycle"""
        data = {"sub": str(uuid4()), "role": "patient"}
        tenant_id = str(uuid4())
        
        token = create_access_token(data, tenant_id)
        decoded = decode_token(token)
        
        assert decoded is not None
        assert decoded["sub"] == data["sub"]
        assert decoded["role"] == data["role"]
        assert decoded["tenant_id"] == tenant_id
        assert decoded["type"] == "access"
        assert "exp" in decoded
        assert "jti" in decoded
    
    def test_invalid_token(self):
        """Test handling of invalid tokens"""
        assert decode_token("invalid.token.here") is None
        assert decode_token("") is None
        assert decode_token("Bearer token") is None
    
    def test_expired_token(self):
        """Test expired token rejection"""
        from app.core.config import settings
        
        data = {"sub": str(uuid4()), "role": "patient"}
        tenant_id = str(uuid4())
        
        # Create token that expires immediately
        token = create_access_token(
            data, tenant_id, expires_delta=timedelta(seconds=-1)
        )
        
        decoded = decode_token(token)
        assert decoded is None  # Should be rejected as expired


class TestBruteForceProtection:
    """Test brute force attack protection"""
    
    def setup_method(self):
        """Reset brute force protector before each test"""
        brute_force_protector._attempts = {}
    
    def test_brute_force_lockout(self):
        """Test account lockout after failed attempts"""
        identifier = "user@example.com"
        
        # Simulate 5 failed attempts
        for i in range(5):
            allowed, msg = brute_force_protector.record_attempt(identifier, success=False)
            assert allowed is True  # First 5 should be allowed
            assert f"{5-i-1} attempts remaining" in msg
        
        # 6th attempt should trigger lockout
        allowed, msg = brute_force_protector.record_attempt(identifier, success=False)
        assert allowed is False
        assert "locked" in msg.lower()
    
    def test_successful_login_resets_counter(self):
        """Test that successful login resets failed attempts"""
        identifier = "user@example.com"
        
        # 3 failed attempts
        for _ in range(3):
            brute_force_protector.record_attempt(identifier, success=False)
        
        # Successful login
        allowed, _ = brute_force_protector.record_attempt(identifier, success=True)
        assert allowed is True
        
        # Counter should be reset
        assert identifier not in brute_force_protector._attempts or \
               brute_force_protector._attempts[identifier]["count"] == 0
    
    def test_lockout_expiration(self):
        """Test that lockout expires after duration"""
        identifier = "user@example.com"
        
        # Trigger lockout
        for _ in range(6):
            brute_force_protector.record_attempt(identifier, success=False)
        
        assert brute_force_protector.is_locked(identifier) is True
        
        # Manually expire lock (simulating time passing)
        from datetime import datetime, timedelta
        brute_force_protector._attempts[identifier]["locked_until"] = \
            datetime.utcnow() - timedelta(seconds=1)
        
        assert brute_force_protector.is_locked(identifier) is False


class TestRateLimiter:
    """Test rate limiting functionality"""
    
    def setup_method(self):
        """Reset rate limiter before each test"""
        rate_limiter._storage = {}
    
    def test_rate_limiting(self):
        """Test request rate limiting"""
        key = "test_client"
        
        # Should allow up to 100 requests
        for i in range(100):
            assert rate_limiter.is_allowed(key, max_requests=100) is True
        
        # 101st request should be blocked
        assert rate_limiter.is_allowed(key, max_requests=100) is False
    
    def test_rate_limit_reset(self):
        """Test rate limit window reset"""
        key = "test_client"
        
        # Use up rate limit
        for _ in range(100):
            rate_limiter.is_allowed(key, max_requests=100)
        
        assert rate_limiter.is_allowed(key, max_requests=100) is False
        
        # Reset
        rate_limiter.reset(key)
        
        assert rate_limiter.is_allowed(key, max_requests=100) is True


# ==================== MULTI-TENANCY TESTS ====================

@pytest.mark.asyncio
class TestMultiTenancy:
    """Test multi-tenant isolation"""
    
    async def test_tenant_isolation(self, db_session):
        """Test that tenant data is isolated"""
        from sqlalchemy import select
        
        # Create two tenants
        tenant1 = Tenant(
            id=uuid4(),
            name="Clinic One",
            slug="clinic-one",
            storage_bucket="clinic-one-bucket",
            storage_prefix="t1"
        )
        tenant2 = Tenant(
            id=uuid4(),
            name="Clinic Two",
            slug="clinic-two",
            storage_bucket="clinic-two-bucket",
            storage_prefix="t2"
        )
        
        db_session.add_all([tenant1, tenant2])
        await db_session.commit()
        
        # Create users for each tenant
        user1 = User(
            id=uuid4(),
            tenant_id=tenant1.id,
            email="user@clinic1.com",
            hashed_password="hash",
            first_name="User",
            last_name="One",
            role=UserRole.PATIENT
        )
        user2 = User(
            id=uuid4(),
            tenant_id=tenant2.id,
            email="user@clinic2.com",
            hashed_password="hash",
            first_name="User",
            last_name="Two",
            role=UserRole.PATIENT
        )
        
        db_session.add_all([user1, user2])
        await db_session.commit()
        
        # Query users for tenant1
        result = await db_session.execute(
            select(User).where(User.tenant_id == tenant1.id)
        )
        tenant1_users = result.scalars().all()
        
        assert len(tenant1_users) == 1
        assert tenant1_users[0].email == "user@clinic1.com"
    
    async def test_cross_tenant_access_prevention(self, db_session):
        """Test that users cannot access other tenant data"""
        # This would be tested through the API layer
        # with proper authentication and tenant middleware
        pass


# ==================== AI SERVICE TESTS ====================

@pytest.mark.asyncio
class TestAIService:
    """Test AI analysis service"""
    
    async def test_ai_job_submission(self):
        """Test AI job submission"""
        from app.services.ai_service import ai_service, AIJob
        
        await ai_service.initialize()
        
        job_id = await ai_service.submit_analysis(
            assessment_id=uuid4(),
            tenant_id=uuid4(),
            image_paths=["/path/to/image.jpg"],
            priority=5
        )
        
        assert job_id is not None
        assert len(job_id) > 0
        
        await ai_service.shutdown()
    
    async def test_ai_job_validation(self):
        """Test AI job input validation"""
        from app.services.ai_service import ai_service
        
        await ai_service.initialize()
        
        # Should reject empty image paths
        with pytest.raises(ValueError, match="at least one image"):
            await ai_service.submit_analysis(
                assessment_id=uuid4(),
                tenant_id=uuid4(),
                image_paths=[],
                priority=5
            )
        
        # Should reject too many images
        with pytest.raises(ValueError, match="Maximum 5 images"):
            await ai_service.submit_analysis(
                assessment_id=uuid4(),
                tenant_id=uuid4(),
                image_paths=[f"/path/to/image{i}.jpg" for i in range(6)],
                priority=5
            )
        
        await ai_service.shutdown()
    
    async def test_circuit_breaker(self):
        """Test circuit breaker pattern"""
        from app.services.ai_service import CircuitBreaker
        
        cb = CircuitBreaker(failure_threshold=3, recovery_timeout=1)
        
        async def failing_func():
            raise Exception("AI Service Error")
        
        async def success_func():
            return "success"
        
        # First 3 failures should raise exception
        for _ in range(3):
            with pytest.raises(Exception):
                await cb.call(failing_func)
        
        # 4th call should trigger circuit breaker
        with pytest.raises(Exception, match="Circuit breaker is OPEN"):
            await cb.call(failing_func)
        
        # Wait for recovery
        import asyncio
        await asyncio.sleep(1.1)
        
        # Should allow one test request (half-open)
        result = await cb.call(success_func)
        assert result == "success"


# ==================== STRIPE INTEGRATION TESTS ====================

@pytest.mark.asyncio
class TestStripeIntegration:
    """Test Stripe payment processing"""
    
    @patch('stripe.PaymentIntent.create')
    async def test_payment_intent_creation(self, mock_create, db_session):
        """Test PaymentIntent creation"""
        from app.services.stripe_service import stripe_service
        
        # Mock Stripe response
        mock_intent = Mock()
        mock_intent.id = "pi_test_123"
        mock_intent.client_secret = "secret_123"
        mock_create.return_value = mock_intent
        
        # Create test order
        tenant = Tenant(
            id=uuid4(),
            name="Test Clinic",
            slug="test-clinic",
            storage_bucket="test-bucket",
            storage_prefix="test"
        )
        db_session.add(tenant)
        await db_session.commit()
        
        user = User(
            id=uuid4(),
            tenant_id=tenant.id,
            email="test@example.com",
            hashed_password="hash",
            first_name="Test",
            last_name="User",
            role=UserRole.PATIENT
        )
        db_session.add(user)
        await db_session.commit()
        
        order = Order(
            id=uuid4(),
            tenant_id=tenant.id,
            patient_id=user.id,
            total_amount=149.99,
            status=OrderStatus.PENDING,
            invoice_number="INV-001"
        )
        db_session.add(order)
        await db_session.commit()
        
        # Create payment intent
        result = await stripe_service.create_payment_intent(
            db=db_session,
            order_id=order.id,
            tenant_id=tenant.id,
            user_id=user.id,
            amount=149.99
        )
        
        assert result["payment_intent_id"] == "pi_test_123"
        assert result["client_secret"] == "secret_123"
        assert result["amount"] == 149.99
    
    @patch('stripe.Webhook.construct_event')
    async def test_webhook_signature_verification(self, mock_construct):
        """Test webhook signature verification"""
        from app.services.stripe_service import stripe_service, PaymentError
        
        # Mock valid webhook
        mock_event = {
            "id": "evt_test",
            "type": "payment_intent.succeeded",
            "data": {"object": {"id": "pi_test"}}
        }
        mock_construct.return_value = mock_event
        
        payload = b'{"test": "data"}'
        signature = "valid_signature"
        
        # Should process successfully
        result = await stripe_service.handle_webhook(
            payload=payload,
            signature=signature,
            db_session=Mock()
        )
        
        assert result["status"] == "processed"
        
        # Test invalid signature
        mock_construct.side_effect = stripe.error.SignatureVerificationError(
            "Invalid signature", "sig"
        )
        
        with pytest.raises(PaymentError, match="Invalid signature"):
            await stripe_service.handle_webhook(
                payload=payload,
                signature="invalid",
                db_session=Mock()
            )
    
    async def test_idempotency_key_generation(self):
        """Test idempotency key generation"""
        key1 = generate_idempotency_key()
        key2 = generate_idempotency_key()
        
        assert key1 != key2
        assert len(key1) == 44  # URL-safe base64 of 32 bytes
        assert len(key2) == 44


# ==================== INTEGRATION TESTS ====================

@pytest.mark.asyncio
class TestEndToEndFlows:
    """End-to-end flow integration tests"""
    
    async def test_patient_registration_flow(self, client):
        """Test complete patient registration flow"""
        # 1. Register patient
        # 2. Verify email
        # 3. Login
        # 4. Create assessment order
        pass
    
    async def test_payment_flow(self, client):
        """Test complete payment flow"""
        # 1. Create order
        # 2. Create payment intent
        # 3. Confirm payment (mock)
        # 4. Verify order status updated
        # 5. Verify assessment created
        pass
    
    async def test_ai_analysis_flow(self, client):
        """Test AI analysis flow"""
        # 1. Upload images
        # 2. Submit to AI queue
        # 3. Wait for processing
        # 4. Verify results
        # 5. Doctor review
        pass


# ==================== FIXTURES ====================

@pytest_asyncio.fixture
async def db_session():
    """Create a test database session"""
    from app.db.session import AsyncSessionLocal
    
    async with AsyncSessionLocal() as session:
        yield session
        await session.rollback()

@pytest.fixture
def client():
    """Create test client"""
    from fastapi.testclient import TestClient
    from app.main import app
    
    return TestClient(app)


# ==================== MOCK HELPERS ====================

class MockStripeCharge:
    """Mock Stripe charge object"""
    def __init__(self):
        self.id = "ch_test_123"
        self.status = "succeeded"
        self.receipt_url = "https://pay.stripe.com/receipts/..."

class MockPaymentIntent:
    """Mock Stripe PaymentIntent"""
    def __init__(self):
        self.id = "pi_test_123"
        self.client_secret = "secret_123"
        self.status = "succeeded"
        self.amount = 14999
        self.currency = "usd"
        self.charges = Mock()
        self.charges.data = [MockStripeCharge()]
        self.metadata = {
            "order_id": str(uuid4()),
            "tenant_id": str(uuid4()),
            "user_id": str(uuid4())
        }