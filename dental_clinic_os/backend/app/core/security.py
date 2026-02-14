"""
Enhanced Security Module with JWT hardening, rate limiting, and brute force protection
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from cryptography.fernet import Fernet
import hashlib
import secrets
import hmac
from app.core.config import settings

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12  # Increased from default 10
)

# Encryption for sensitive data - generate valid key if not provided
def _get_fernet_key():
    """Get or generate valid Fernet key"""
    key = getattr(settings, 'ENCRYPTION_KEY', None)
    if key:
        try:
            # Validate the key
            return Fernet(key.encode())
        except Exception:
            pass
    # Generate a valid key
    return Fernet(Fernet.generate_key())

fernet = _get_fernet_key()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password with constant-time comparison"""
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        return False

def get_password_hash(password: str) -> str:
    """Generate secure password hash"""
    # Validate password strength
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters")
    if not any(c.isupper() for c in password):
        raise ValueError("Password must contain uppercase letter")
    if not any(c.islower() for c in password):
        raise ValueError("Password must contain lowercase letter")
    if not any(c.isdigit() for c in password):
        raise ValueError("Password must contain digit")
    if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
        raise ValueError("Password must contain special character")
    
    return pwd_context.hash(password)

def create_access_token(data: Dict[str, Any], tenant_id: Optional[str] = None, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token with tenant context"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Add token metadata
    to_encode.update({
        "exp": expire,
        "type": "access",
        "iat": datetime.utcnow(),
        "jti": secrets.token_urlsafe(16)  # Unique token ID for revocation
    })
    
    # Add tenant_id if provided
    if tenant_id:
        to_encode["tenant_id"] = tenant_id
    
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: Dict[str, Any], tenant_id: Optional[str] = None) -> str:
    """Create JWT refresh token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({
        "exp": expire,
        "type": "refresh",
        "iat": datetime.utcnow(),
        "jti": secrets.token_urlsafe(16)
    })
    
    # Add tenant_id if provided
    if tenant_id:
        to_encode["tenant_id"] = tenant_id
    
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and validate JWT token"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        
        # Check token type
        if payload.get("type") not in ["access", "refresh"]:
            return None
        
        # Check expiration
        exp = payload.get("exp")
        if not exp or datetime.utcnow() > datetime.fromtimestamp(exp):
            return None
        
        return payload
    except JWTError:
        return None

def verify_refresh_token_rotation(old_token: str, new_token: str) -> bool:
    """Verify refresh token rotation (prevent replay attacks)"""
    old_payload = decode_token(old_token)
    new_payload = decode_token(new_token)
    
    if not old_payload or not new_payload:
        return False
    
    # Verify same user
    if old_payload.get("sub") != new_payload.get("sub"):
        return False
    
    # Verify same tenant if present in both tokens
    old_tenant = old_payload.get("tenant_id")
    new_tenant = new_payload.get("tenant_id")
    if old_tenant and new_tenant and old_tenant != new_tenant:
        return False
    
    return True

def generate_idempotency_key() -> str:
    """Generate unique idempotency key for Stripe operations"""
    return secrets.token_urlsafe(32)

def hash_sensitive_data(data: str) -> str:
    """One-way hash for sensitive data storage"""
    return hashlib.sha256(data.encode()).hexdigest()

def encrypt_sensitive_data(data: str) -> str:
    """Encrypt sensitive data for storage"""
    return fernet.encrypt(data.encode()).decode()

def decrypt_sensitive_data(encrypted_data: str) -> str:
    """Decrypt sensitive data"""
    return fernet.decrypt(encrypted_data.encode()).decode()

def verify_webhook_signature(payload: bytes, signature: str, secret: str) -> bool:
    """Verify Stripe webhook signature"""
    try:
        expected_signature = hmac.new(
            secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)
    except Exception:
        return False

def generate_secure_random_string(length: int = 32) -> str:
    """Generate cryptographically secure random string"""
    return secrets.token_urlsafe(length)

class RateLimiter:
    """Simple in-memory rate limiter (use Redis in production)"""
    
    def __init__(self):
        self._storage: Dict[str, Dict] = {}
    
    def is_allowed(self, key: str, max_requests: int = 100, window_seconds: int = 60) -> bool:
        """Check if request is within rate limit"""
        now = datetime.utcnow()
        
        if key not in self._storage:
            self._storage[key] = {
                "count": 1,
                "window_start": now
            }
            return True
        
        entry = self._storage[key]
        window_end = entry["window_start"] + timedelta(seconds=window_seconds)
        
        if now > window_end:
            # Reset window
            entry["count"] = 1
            entry["window_start"] = now
            return True
        
        if entry["count"] < max_requests:
            entry["count"] += 1
            return True
        
        return False
    
    def reset(self, key: str):
        """Reset rate limit for key"""
        if key in self._storage:
            del self._storage[key]

# Global rate limiter instance
rate_limiter = RateLimiter()

class BruteForceProtector:
    """Protect against brute force attacks"""
    
    MAX_ATTEMPTS = 5
    LOCKOUT_DURATION = timedelta(minutes=30)
    
    def __init__(self):
        self._attempts: Dict[str, Dict] = {}
    
    def record_attempt(self, identifier: str, success: bool) -> tuple[bool, Optional[str]]:
        """
        Record authentication attempt
        Returns: (is_allowed, error_message)
        """
        now = datetime.utcnow()
        
        if identifier not in self._attempts:
            self._attempts[identifier] = {
                "count": 0,
                "locked_until": None,
                "last_attempt": now
            }
        
        entry = self._attempts[identifier]
        
        # Check if still locked
        if entry["locked_until"] and now < entry["locked_until"]:
            remaining = (entry["locked_until"] - now).seconds // 60
            return False, f"Account locked. Try again in {remaining} minutes."
        
        # Reset if lock expired
        if entry["locked_until"] and now >= entry["locked_until"]:
            entry["count"] = 0
            entry["locked_until"] = None
        
        if success:
            # Reset on successful login
            entry["count"] = 0
            entry["locked_until"] = None
            return True, None
        
        # Record failed attempt
        entry["count"] += 1
        entry["last_attempt"] = now
        
        if entry["count"] >= self.MAX_ATTEMPTS:
            entry["locked_until"] = now + self.LOCKOUT_DURATION
            return False, f"Too many failed attempts. Account locked for 30 minutes."
        
        remaining = self.MAX_ATTEMPTS - entry["count"]
        return True, f"Invalid credentials. {remaining} attempts remaining."
    
    def is_locked(self, identifier: str) -> bool:
        """Check if identifier is currently locked"""
        if identifier not in self._attempts:
            return False
        
        entry = self._attempts[identifier]
        if entry["locked_until"] and datetime.utcnow() < entry["locked_until"]:
            return True
        
        return False

# Global brute force protector
brute_force_protector = BruteForceProtector()