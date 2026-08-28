from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, require_admin
from app.core.config import settings
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
from app.models.user import User, UserRole, BuyerStatus
from app.schemas.auth import (
    UserCreate,
    UserLogin,
    Token,
    RefreshTokenRequest,
    UserResponse,
    BuyerApprovalRequest,
    BuyerListResponse,
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
        company_name=user_data.company_name,
        company_tax_id=user_data.company_tax_id,
        company_address=user_data.company_address,
        phone=user_data.phone,
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
    if user.role == UserRole.buyer and settings.REQUIRE_BUYER_APPROVAL:
        if user.buyer_status == BuyerStatus.pending:
            raise HTTPException(status_code=403, detail="Buyer account pending approval")
        if user.buyer_status == BuyerStatus.rejected:
            raise HTTPException(status_code=403, detail=f"Buyer account rejected: {user.buyer_rejection_reason or ''}")
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


@router.get("/config", tags=["config"])
def get_config():
    return {
        "require_login_to_see_prices": settings.REQUIRE_LOGIN_TO_SEE_PRICES,
        "require_buyer_approval": settings.REQUIRE_BUYER_APPROVAL,
        "allow_cod_only": settings.ALLOW_CASH_ON_DELIVERY_ONLY,
    }


# Buyer approval endpoints (admin only)
@router.get("/buyers/pending", response_model=list[BuyerListResponse])
def list_pending_buyers(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    buyers = db.query(User).filter(User.role == UserRole.buyer, User.buyer_status == BuyerStatus.pending).all()
    return [
        BuyerListResponse(
            id=b.id,
            email=b.email,
            full_name=b.full_name,
            company_name=b.company_name,
            status=b.buyer_status,
            created_at=b.created_at,
        )
        for b in buyers
    ]


@router.post("/buyers/{buyer_id}/approve", response_model=UserResponse)
def approve_buyer(
    buyer_id: str,
    payload: BuyerApprovalRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    from uuid import UUID as UUUID

    try:
        uid = UUUID(buyer_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid buyer id")
    buyer = db.query(User).filter(User.id == uid, User.role == UserRole.buyer).first()
    if not buyer:
        raise HTTPException(status_code=404, detail="Buyer not found")
    if payload.status == BuyerStatus.approved:
        buyer.buyer_status = BuyerStatus.approved
        buyer.buyer_rejection_reason = None
        buyer.is_active = True
    elif payload.status == BuyerStatus.rejected:
        if not payload.rejection_reason:
            raise HTTPException(status_code=400, detail="Rejection reason required")
        buyer.buyer_status = BuyerStatus.rejected
        buyer.buyer_rejection_reason = payload.rejection_reason
        buyer.is_active = False
    else:
        raise HTTPException(status_code=400, detail="Invalid status")
    db.commit()
    db.refresh(buyer)
    return buyer


@router.get("/buyers", response_model=list[BuyerListResponse])
def list_all_buyers(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    buyers = db.query(User).filter(User.role == UserRole.buyer).order_by(User.created_at.desc()).all()
    return [
        BuyerListResponse(
            id=b.id,
            email=b.email,
            full_name=b.full_name,
            company_name=b.company_name,
            status=b.buyer_status,
            created_at=b.created_at,
        )
        for b in buyers
    ]