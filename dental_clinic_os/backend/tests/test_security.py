import pytest
from datetime import datetime, timedelta
from jose import jwt

from app.core.security import (
    verify_password, get_password_hash, create_access_token,
    create_refresh_token, decode_token
)
from app.core.config import settings

def test_password_hashing():
    """Test password hashing and verification"""
    password = "testpassword123"
    hashed = get_password_hash(password)
    
    # Verify correct password
    assert verify_password(password, hashed) is True
    
    # Verify wrong password fails
    assert verify_password("wrongpassword", hashed) is False

def test_access_token_creation():
    """Test JWT access token creation and decoding"""
    data = {"sub": "123", "role": "patient"}
    token = create_access_token(data)
    
    # Decode and verify
    decoded = decode_token(token)
    assert decoded is not None
    assert decoded["sub"] == "123"
    assert decoded["role"] == "patient"
    assert decoded["type"] == "access"
    
    # Check expiration
    exp = datetime.fromtimestamp(decoded["exp"])
    assert exp > datetime.utcnow()
    assert exp < datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES + 1)

def test_refresh_token_creation():
    """Test JWT refresh token creation"""
    data = {"sub": "123", "role": "patient"}
    token = create_refresh_token(data)
    
    decoded = decode_token(token)
    assert decoded is not None
    assert decoded["type"] == "refresh"

def test_invalid_token():
    """Test decoding invalid token"""
    invalid_token = "invalid.token.here"
    decoded = decode_token(invalid_token)
    assert decoded is None

@pytest.mark.asyncio
async def test_database_connection():
    """Test database connection"""
    from app.db.session import async_engine
    
    async with async_engine.connect() as conn:
        result = await conn.execute("SELECT 1")
        assert result.scalar() == 1