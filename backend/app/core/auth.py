import asyncio
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

import jwt
from jwt import PyJWTError as JWTError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.user import User, UserRole, BuyerStatus
from app.models.email_verification_token import EmailVerificationToken
from app.models.password_reset_token import PasswordResetToken

# Current target iteration count for new/rehashed passwords. Hashes store their
# own iteration count (see format below), so this can be raised again later
# without invalidating existing accounts — verify_password always reads the
# count that was actually used to create the hash it's checking against.
PBKDF2_ITERATIONS = 600_000
# Iteration count implied by the legacy 2-part hash format (salt$hash) used
# before this constant existed — never change this; it describes hashes
# already stored in the database, not new ones.
_LEGACY_ITERATIONS = 100_000


def _parse_hash(hashed_password: str) -> tuple[int, bytes, str]:
    """Returns (iterations, salt_bytes, hash_hex). Supports both the legacy
    2-part "salt$hash" format (implicitly 100k iterations) and the current
    3-part "iterations$salt$hash" format, so already-issued password hashes
    keep verifying correctly after PBKDF2_ITERATIONS is raised."""
    parts = hashed_password.split("$")
    if len(parts) == 2:
        salt, hash_val = parts
        return _LEGACY_ITERATIONS, bytes.fromhex(salt), hash_val
    iterations, salt, hash_val = parts
    return int(iterations), bytes.fromhex(salt), hash_val


def verify_password(plain_password: str, hashed_password: str) -> bool:
    iterations, salt, hash_val = _parse_hash(hashed_password)
    computed = hashlib.pbkdf2_hmac("sha256", plain_password.encode(), salt, iterations).hex()
    # Constant-time compare — a plain `==` short-circuits on the first
    # mismatched byte, which leaks a timing signal about how much of a
    # guessed hash was correct.
    return hmac.compare_digest(computed, hash_val)


def needs_rehash(hashed_password: str) -> bool:
    """True when a stored hash was created with a weaker (legacy) iteration
    count than the current target — used to opportunistically upgrade a
    user's hash to PBKDF2_ITERATIONS the next time they successfully log in,
    without ever requiring a forced password reset."""
    iterations, _, _ = _parse_hash(hashed_password)
    return iterations < PBKDF2_ITERATIONS


def get_password_hash(password: str) -> str:
    salt = secrets.token_bytes(16)
    hash_val = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, PBKDF2_ITERATIONS).hex()
    return f"{PBKDF2_ITERATIONS}${salt.hex()}${hash_val}"


async def verify_password_async(plain_password: str, hashed_password: str) -> bool:
    """Async wrapper — runs the CPU-bound PBKDF2 check in a thread pool so the
    event loop is not blocked during the ~1-3 s hashing operation."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, verify_password, plain_password, hashed_password)


async def get_password_hash_async(password: str) -> str:
    """Async wrapper — runs the CPU-bound PBKDF2 hash in a thread pool."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, get_password_hash, password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None


def create_tokens(user: User) -> tuple[str, str]:
    # "tv" (token_version) is checked against the user's current token_version
    # on every request (see get_current_user / refresh) — bumping it on
    # password change instantly revokes every token minted before that point.
    token_data = {"sub": str(user.id), "role": user.role.value, "tv": user.token_version}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    return access_token, refresh_token


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()


def get_user_by_id(db: Session, user_id: UUID) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    user = get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def create_user(
    db: Session,
    email: str,
    password: str,
    full_name: str,
    role: UserRole = UserRole.buyer,
    company_name: Optional[str] = None,
    company_tax_id: Optional[str] = None,
    company_address: Optional[str] = None,
    phone: Optional[str] = None,
) -> User:
    hashed_password = get_password_hash(password)
    buyer_status = BuyerStatus.approved
    if role == UserRole.buyer and settings.REQUIRE_BUYER_APPROVAL:
        buyer_status = BuyerStatus.pending
    user = User(
        email=email,
        hashed_password=hashed_password,
        full_name=full_name,
        role=role,
        buyer_status=buyer_status,
        company_name=company_name,
        company_tax_id=company_tax_id,
        company_address=company_address,
        phone=phone,
    )
    db.add(user)
    db.flush()
    return user


async def create_user_async(
    db: Session,
    email: str,
    password: str,
    full_name: str,
    role: UserRole = UserRole.buyer,
    company_name: Optional[str] = None,
    company_tax_id: Optional[str] = None,
    company_address: Optional[str] = None,
    phone: Optional[str] = None,
) -> User:
    """Async version of create_user — hashes the password off the event loop."""
    hashed_password = await get_password_hash_async(password)
    buyer_status = BuyerStatus.approved
    if role == UserRole.buyer and settings.REQUIRE_BUYER_APPROVAL:
        buyer_status = BuyerStatus.pending
    user = User(
        email=email,
        hashed_password=hashed_password,
        full_name=full_name,
        role=role,
        buyer_status=buyer_status,
        company_name=company_name,
        company_tax_id=company_tax_id,
        company_address=company_address,
        phone=phone,
    )
    db.add(user)
    db.flush()
    return user


def create_verification_token(db: Session, user: User) -> str:
    """Create a new email verification token for user and return the raw token."""
    # Generate a cryptographically secure random token
    raw_token = secrets.token_urlsafe(32)
    
    # Hash the token before storing (SHA-256)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    
    # Set expiration to 24 hours from now
    expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
    
    # Create the token record
    verification_token = EmailVerificationToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=expires_at
    )
    
    db.add(verification_token)
    db.flush()
    
    return raw_token


def verify_email_token(db: Session, raw_token: str) -> Optional[User]:
    """Verify an email verification token and mark user as verified if valid."""
    # Hash the provided token to compare with stored hash
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    
    # Find the token record
    token = db.query(EmailVerificationToken).filter(
        EmailVerificationToken.token_hash == token_hash,
        EmailVerificationToken.used_at.is_(None)  # Not already used
    ).first()
    
    if not token:
        return None
    
    # Check if token is expired (handle timezone-naive datetime from SQLite)
    now = datetime.now(timezone.utc)
    token_expires = token.expires_at
    if not token_expires.tzinfo:
        # If token expires_at is timezone-naive, treat it as UTC
        token_expires = token_expires.replace(tzinfo=timezone.utc)
    
    if token_expires < now:
        return None
    
    # Get the user
    user = db.query(User).filter(User.id == token.user_id).first()
    if not user:
        return None
    
    # Mark token as used and user as verified
    token.used_at = now
    user.email_verified = True
    
    db.flush()
    return user


def invalidate_user_verification_tokens(db: Session, user_id: UUID) -> None:
    """Mark all existing verification tokens for a user as used."""
    now = datetime.now(timezone.utc)
    db.query(EmailVerificationToken).filter(
        EmailVerificationToken.user_id == user_id,
        EmailVerificationToken.used_at.is_(None)
    ).update({"used_at": now})
    db.flush()


# ── Password reset (forgot password) ───────────────────────────────────────
# Same hash-and-store-only-the-hash pattern as email verification tokens: the
# raw token only ever exists in the outbound email and the requesting
# browser's URL bar, never in the database, so a DB leak can't be used to
# forge reset links.

def create_password_reset_token(db: Session, user: User) -> str:
    """Create a new password reset token for user and return the raw token."""
    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

    reset_token = PasswordResetToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=expires_at,
    )
    db.add(reset_token)
    db.flush()
    return raw_token


def verify_password_reset_token(db: Session, raw_token: str) -> Optional[User]:
    """Return the user for a valid, unused, unexpired reset token, else None.
    Does not consume the token — call invalidate_user_password_reset_tokens
    once the new password has actually been set."""
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()

    token = db.query(PasswordResetToken).filter(
        PasswordResetToken.token_hash == token_hash,
        PasswordResetToken.used_at.is_(None),
    ).first()
    if not token:
        return None

    now = datetime.now(timezone.utc)
    token_expires = token.expires_at
    if not token_expires.tzinfo:
        token_expires = token_expires.replace(tzinfo=timezone.utc)
    if token_expires < now:
        return None

    user = db.query(User).filter(User.id == token.user_id).first()
    if not user:
        return None

    return user


def invalidate_user_password_reset_tokens(db: Session, user_id: UUID) -> None:
    """Mark all existing password reset tokens for a user as used — called
    whenever a new one is issued, so only the most recently requested link
    can ever be used, and again after a successful reset for good measure."""
    now = datetime.now(timezone.utc)
    db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user_id,
        PasswordResetToken.used_at.is_(None),
    ).update({"used_at": now})
    db.flush()

