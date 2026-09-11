from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.auth import decode_token, get_user_by_id
from app.db.session import get_db
from app.models.user import User, UserRole
from app.core.config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_PREFIX}/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        raise credentials_exception
    user_id: str = payload.get("sub")
    if user_id is None:
        raise credentials_exception
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise credentials_exception
    user = get_user_by_id(db, user_uuid)
    if user is None:
        raise credentials_exception
    # A token minted before the user's last password change carries a stale
    # "tv" claim — reject it so a stolen/leaked token stops working the
    # moment the password is changed, instead of staying valid for its full
    # remaining lifetime (up to REFRESH_TOKEN_EXPIRE_DAYS for a refresh token).
    # Tokens issued before this field existed carry no "tv" claim at all;
    # default that to 0 so they keep working (token_version starts at 0 for
    # every user, so a missing claim and an explicit 0 mean the same thing —
    # this avoids force-logging-out every already-signed-in user on deploy).
    if payload.get("tv", 0) != user.token_version:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated",
        )
    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    return current_user


def require_role(*allowed_roles: UserRole):
    def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role {current_user.role.value} not authorized for this action",
            )
        return current_user
    return role_checker


require_buyer = require_role(UserRole.buyer)
require_seller = require_role(UserRole.seller)
require_admin = require_role(UserRole.admin)
require_seller_or_admin = require_role(UserRole.seller, UserRole.admin)