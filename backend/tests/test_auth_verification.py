import pytest
from unittest.mock import AsyncMock, patch, ANY
from datetime import datetime, timezone, timedelta
from uuid import uuid4

from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from app.main import app
from app.models.user import User, UserRole
from app.models.email_verification_token import EmailVerificationToken
from app.core.auth import (
    create_verification_token, 
    verify_email_token, 
    invalidate_user_verification_tokens,
    get_password_hash
)


client = TestClient(app)


def test_create_verification_token(db_session: Session):
    """Test creating a verification token."""
    # Create a test user
    user = User(
        id=uuid4(),
        email="test@example.com",
        hashed_password=get_password_hash("password123"),
        full_name="Test User",
        role=UserRole.buyer,
        email_verified=False
    )
    db_session.add(user)
    db_session.commit()
    
    # Create verification token
    raw_token = create_verification_token(db_session, user)
    
    # Verify token properties
    assert len(raw_token) > 20  # Should be a substantial token
    assert isinstance(raw_token, str)
    
    # Verify token was stored in database
    token_record = db_session.query(EmailVerificationToken).filter(
        EmailVerificationToken.user_id == user.id
    ).first()
    
    assert token_record is not None
    assert token_record.user_id == user.id
    assert token_record.used_at is None
    # Handle timezone comparison for SQLite (naive datetime)
    expires_at_utc = token_record.expires_at.replace(tzinfo=timezone.utc) if not token_record.expires_at.tzinfo else token_record.expires_at
    assert expires_at_utc > datetime.now(timezone.utc)
    
    # Verify token hash is correct length (SHA-256 = 64 hex chars)
    assert len(token_record.token_hash) == 64


def test_verify_email_token_success(db_session: Session):
    """Test successful email verification."""
    # Create user
    user = User(
        id=uuid4(),
        email="test@example.com",
        hashed_password=get_password_hash("password123"),
        full_name="Test User",
        role=UserRole.buyer,
        email_verified=False
    )
    db_session.add(user)
    db_session.commit()
    
    # Create token
    raw_token = create_verification_token(db_session, user)
    db_session.commit()
    
    # Verify token
    verified_user = verify_email_token(db_session, raw_token)
    
    assert verified_user is not None
    assert verified_user.id == user.id
    assert verified_user.email_verified is True
    
    # Check that token is marked as used
    token_record = db_session.query(EmailVerificationToken).filter(
        EmailVerificationToken.user_id == user.id
    ).first()
    assert token_record.used_at is not None


def test_verify_email_token_invalid(db_session: Session):
    """Test verification with invalid token."""
    result = verify_email_token(db_session, "invalid_token_12345")
    assert result is None


def test_verify_email_token_expired(db_session: Session):
    """Test verification with expired token."""
    # Create user
    user = User(
        id=uuid4(),
        email="test@example.com",
        hashed_password=get_password_hash("password123"),
        full_name="Test User",
        role=UserRole.buyer,
        email_verified=False
    )
    db_session.add(user)
    db_session.flush()
    
    # Create an expired token manually
    import hashlib
    raw_token = "expired_token_test"
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    
    expired_token = EmailVerificationToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=datetime.now(timezone.utc) - timedelta(hours=1)  # Expired 1 hour ago
    )
    db_session.add(expired_token)
    db_session.commit()
    
    # Try to verify expired token
    result = verify_email_token(db_session, raw_token)
    assert result is None


def test_verify_email_token_already_used(db_session: Session):
    """Test verification with already used token."""
    # Create user
    user = User(
        id=uuid4(),
        email="test@example.com",
        hashed_password=get_password_hash("password123"),
        full_name="Test User",
        role=UserRole.buyer,
        email_verified=False
    )
    db_session.add(user)
    db_session.commit()
    
    # Create and use token
    raw_token = create_verification_token(db_session, user)
    db_session.commit()
    
    # Use token once
    first_result = verify_email_token(db_session, raw_token)
    assert first_result is not None
    
    # Try to use same token again
    second_result = verify_email_token(db_session, raw_token)
    assert second_result is None


def test_invalidate_user_verification_tokens(db_session: Session):
    """Test invalidating all tokens for a user."""
    # Create user
    user = User(
        id=uuid4(),
        email="test@example.com",
        hashed_password=get_password_hash("password123"),
        full_name="Test User",
        role=UserRole.buyer,
        email_verified=False
    )
    db_session.add(user)
    db_session.commit()
    
    # Create multiple tokens
    token1 = create_verification_token(db_session, user)
    token2 = create_verification_token(db_session, user)
    db_session.commit()
    
    # Verify both tokens exist and are unused
    unused_count = db_session.query(EmailVerificationToken).filter(
        EmailVerificationToken.user_id == user.id,
        EmailVerificationToken.used_at.is_(None)
    ).count()
    assert unused_count == 2
    
    # Invalidate all tokens
    invalidate_user_verification_tokens(db_session, user.id)
    db_session.commit()
    
    # Verify all tokens are now marked as used
    unused_count = db_session.query(EmailVerificationToken).filter(
        EmailVerificationToken.user_id == user.id,
        EmailVerificationToken.used_at.is_(None)
    ).count()
    assert unused_count == 0
    
    # Verify tokens can't be used anymore
    assert verify_email_token(db_session, token1) is None
    assert verify_email_token(db_session, token2) is None


@pytest.mark.asyncio
async def test_signup_sends_verification_email():
    """Test that signup endpoint sends verification email."""
    with patch('app.api.routes.auth.send_verification_email', new=AsyncMock()) as mock_send:
        response = client.post("/api/v1/auth/signup", json={
            "email": "newuser@example.com",
            "password": "password123",
            "full_name": "New User"
        })
        
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["email_verified"] is False
        
        # Verify verification email was sent
        mock_send.assert_called_once()
        call_args = mock_send.call_args[0]
        assert call_args[0] == "newuser@example.com"
        assert call_args[1] == "New User"
        assert len(call_args[2]) > 20  # Token should be substantial


def test_verify_email_endpoint_success():
    """Test the verify-email endpoint with valid token."""
    # First create a user and token (using test database)
    with patch('app.api.routes.auth.verify_email_token') as mock_verify:
        # Mock successful verification
        mock_user = type('User', (), {
            'id': uuid4(),
            'email': 'test@example.com',
            'full_name': 'Test User',
            'role': UserRole.buyer,
            'is_active': True,
            'buyer_status': 'approved',
            'email_verified': True,
            'company_name': None,
            'company_tax_id': None, 
            'company_address': None,
            'phone': None,
            'created_at': datetime.now(timezone.utc)
        })()
        mock_verify.return_value = mock_user
        
        response = client.get("/api/v1/auth/verify-email?token=valid_token_123")
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Email verified successfully"
        assert data["user"]["email_verified"] is True
        
        mock_verify.assert_called_once_with(ANY, "valid_token_123")


def test_verify_email_endpoint_invalid_token():
    """Test the verify-email endpoint with invalid token."""
    with patch('app.api.routes.auth.verify_email_token') as mock_verify:
        mock_verify.return_value = None  # Invalid token
        
        response = client.get("/api/v1/auth/verify-email?token=invalid_token")
        
        assert response.status_code == 400
        data = response.json()
        assert "Invalid or expired verification token" in data["detail"]


def test_resend_verification_already_verified():
    """Test resend verification for already verified user."""
    # Mock an already verified user
    with patch('app.api.dependencies.get_current_user') as mock_get_user:
        mock_user = type('User', (), {
            'id': uuid4(),
            'email': 'verified@example.com',
            'email_verified': True
        })()
        mock_get_user.return_value = mock_user
        
        response = client.post("/api/v1/auth/resend-verification", 
                              headers={"Authorization": "Bearer fake_token"})
        
        assert response.status_code == 400
        data = response.json()
        assert "already verified" in data["detail"]


@pytest.mark.asyncio 
async def test_resend_verification_success():
    """Test successful resend verification."""
    with patch('app.api.dependencies.get_current_user') as mock_get_user, \
         patch('app.api.routes.auth.invalidate_user_verification_tokens') as mock_invalidate, \
         patch('app.api.routes.auth.create_verification_token') as mock_create, \
         patch('app.api.routes.auth.send_verification_email', new=AsyncMock()) as mock_send:
        
        mock_user = type('User', (), {
            'id': uuid4(),
            'email': 'unverified@example.com',
            'full_name': 'Unverified User',
            'email_verified': False
        })()
        mock_get_user.return_value = mock_user
        mock_create.return_value = "new_token_123"
        
        response = client.post("/api/v1/auth/resend-verification",
                              headers={"Authorization": "Bearer fake_token"})
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Verification email sent successfully"
        
        # Verify the flow
        mock_invalidate.assert_called_once_with(ANY, mock_user.id)
        mock_create.assert_called_once_with(ANY, mock_user)
        mock_send.assert_called_once_with(
            mock_user.email, 
            mock_user.full_name, 
            "new_token_123"
        )