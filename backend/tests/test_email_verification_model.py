import pytest
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from app.models.email_verification_token import EmailVerificationToken


def test_user_email_verified_field(db_session: Session):
    """Test that the email_verified field works correctly on User model."""
    user = User(
        id=uuid4(),
        email="test@example.com",
        hashed_password="hashed_password",
        full_name="Test User",
        role=UserRole.buyer,
        email_verified=False
    )
    db_session.add(user)
    db_session.commit()
    
    # Verify default value
    assert user.email_verified is False
    
    # Test updating the field
    user.email_verified = True
    db_session.commit()
    
    # Refresh and verify
    db_session.refresh(user)
    assert user.email_verified is True


def test_email_verification_token_model(db_session: Session):
    """Test EmailVerificationToken model creation and relationships."""
    # Create a user first
    user = User(
        id=uuid4(),
        email="test@example.com", 
        hashed_password="hashed_password",
        full_name="Test User",
        role=UserRole.buyer,
        email_verified=False
    )
    db_session.add(user)
    db_session.flush()
    
    # Create a verification token
    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
    
    token = EmailVerificationToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=expires_at
    )
    db_session.add(token)
    db_session.commit()
    
    # Verify the token was created correctly
    assert token.id is not None
    assert token.user_id == user.id
    assert token.token_hash == token_hash
    # SQLite doesn't preserve timezone info, so compare without timezone
    assert token.expires_at.replace(tzinfo=timezone.utc) == expires_at
    assert token.used_at is None
    assert token.created_at is not None
    assert token.updated_at is not None
    
    # Test relationship
    assert token.user == user
    assert len(user.verification_tokens) == 1
    assert user.verification_tokens[0] == token


def test_token_hash_storage(db_session: Session):
    """Test that token hash is stored correctly and raw token is not stored."""
    user = User(
        id=uuid4(),
        email="test@example.com",
        hashed_password="hashed_password", 
        full_name="Test User",
        role=UserRole.buyer
    )
    db_session.add(user)
    db_session.flush()
    
    # Generate token and hash
    raw_token = secrets.token_urlsafe(32)
    expected_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    
    token = EmailVerificationToken(
        user_id=user.id,
        token_hash=expected_hash,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24)
    )
    db_session.add(token)
    db_session.commit()
    
    # Verify hash is stored, not raw token
    assert token.token_hash == expected_hash
    assert len(token.token_hash) == 64  # SHA-256 produces 64 hex chars
    assert raw_token not in token.token_hash  # Raw token should not be in hash


def test_token_expiry_and_usage(db_session: Session):
    """Test token expiry and usage timestamps."""
    user = User(
        id=uuid4(),
        email="test@example.com",
        hashed_password="hashed_password",
        full_name="Test User", 
        role=UserRole.buyer
    )
    db_session.add(user)
    db_session.flush()
    
    # Create an expired token
    expired_token = EmailVerificationToken(
        user_id=user.id,
        token_hash=hashlib.sha256(b"expired_token").hexdigest(),
        expires_at=datetime.now(timezone.utc) - timedelta(hours=1)  # 1 hour ago
    )
    
    # Create a valid token
    valid_token = EmailVerificationToken(
        user_id=user.id,
        token_hash=hashlib.sha256(b"valid_token").hexdigest(),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24)  # 24 hours from now
    )
    
    db_session.add_all([expired_token, valid_token])
    db_session.commit()
    
    # Test expiry check (handle timezone-naive comparison for SQLite)
    now = datetime.now(timezone.utc)
    assert expired_token.expires_at < now.replace(tzinfo=None)  # Token is expired
    assert valid_token.expires_at > now.replace(tzinfo=None)    # Token is still valid
    
    # Test marking as used
    used_time = datetime.now(timezone.utc)
    valid_token.used_at = used_time
    db_session.commit()
    
    # SQLite stores as naive datetime, so compare accordingly
    assert valid_token.used_at.replace(tzinfo=timezone.utc) == used_time
    assert expired_token.used_at is None


def test_cascade_delete_tokens_on_user_delete(db_session: Session):
    """Test that verification tokens are deleted when user is deleted."""
    user = User(
        id=uuid4(),
        email="test@example.com",
        hashed_password="hashed_password",
        full_name="Test User",
        role=UserRole.buyer
    )
    db_session.add(user)
    db_session.flush()
    
    # Create multiple tokens for the user
    token1 = EmailVerificationToken(
        user_id=user.id,
        token_hash=hashlib.sha256(b"token1").hexdigest(),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24)
    )
    token2 = EmailVerificationToken(
        user_id=user.id,
        token_hash=hashlib.sha256(b"token2").hexdigest(),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24)
    )
    
    db_session.add_all([token1, token2])
    db_session.commit()
    
    # Verify tokens exist
    tokens_count = db_session.query(EmailVerificationToken).filter(
        EmailVerificationToken.user_id == user.id
    ).count()
    assert tokens_count == 2
    
    # Delete the user
    db_session.delete(user)
    db_session.commit()
    
    # Verify tokens are cascade deleted
    remaining_tokens = db_session.query(EmailVerificationToken).filter(
        EmailVerificationToken.user_id == user.id
    ).count()
    assert remaining_tokens == 0