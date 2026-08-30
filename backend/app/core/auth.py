from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID
import hashlib
import secrets

from jose import jwt, JWTError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.user import User, UserRole, BuyerStatus


def verify_password(plain_password: str, hashed_password: str) -> bool:
    salt, hash_val = hashed_password.split("$")
    return hashlib.pbkdf2_hmac("sha256", plain_password.encode(), bytes.fromhex(salt), 100000).hex() == hash_val


def get_password_hash(password: str) -> str:
    salt = secrets.token_bytes(16)
    hash_val = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100000).hex()
    return f"{salt.hex()}${hash_val}"


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
    token_data = {"sub": str(user.id), "role": user.role.value}
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

