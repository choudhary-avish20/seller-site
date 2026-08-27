from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.core.auth import (
    authenticate_user,
    create_user,
    create_tokens,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_user_by_email,
)
from app.models.user import User, UserRole
from app.schemas.auth import (
    UserCreate,
    UserLogin,
    Token,
    RefreshTokenRequest,
    UserResponse,
)


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def signup(user_data: UserCreate, db: Session = Depends(get_db)):
    if get_user_by_email(db, user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    if user_data.role == UserRole.seller:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Seller registration requires business info. Use /auth/register-seller endpoint.",
        )
    user = create_user(
        db=db,
        email=user_data.email,
        password=user_data.password,
        full_name=user_data.full_name,
        role=user_data.role,
    )
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=Token)
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    user = authenticate_user(db, credentials.email, credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated",
        )
    access_token, refresh_token = create_tokens(user)
    return Token(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=Token)
def refresh_token(request: RefreshTokenRequest):
    payload = decode_token(request.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )
    user_id = payload.get("sub")
    role = payload.get("role")
    new_access = create_access_token({"sub": user_id, "role": role})
    new_refresh = create_refresh_token({"sub": user_id, "role": role})
    return Token(access_token=new_access, refresh_token=new_refresh)


@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    return current_user