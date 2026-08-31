from fastapi import APIRouter, Depends, HTTPException, status, Query
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
    get_password_hash,
    verify_password,
    create_verification_token,
    verify_email_token,
    invalidate_user_verification_tokens,
)
from app.models.user import User, UserRole, BuyerStatus
from app.models.seller import SellerProfile, SellerStatus
from app.schemas.auth import (
    UserCreate,
    UserLogin,
    Token,
    RefreshTokenRequest,
    UserResponse,
    BuyerApprovalRequest,
    BuyerListResponse,
    EmailVerifyResponse,
    ResendVerificationResponse,
    PasswordChangeRequest,
    MessageResponse,
)
from app.services.email import send_verification_email


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(user_data: UserCreate, db: Session = Depends(get_db)):
    if get_user_by_email(db, user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    # Bug #3 fix: ignore any role the client sends — this endpoint always creates buyers.
    # Self-assigning admin or seller via this route is not allowed.
    if user_data.role in (UserRole.seller, UserRole.admin):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Seller registration requires business info. Use /sellers/register endpoint."
                if user_data.role == UserRole.seller
                else "Cannot self-register as admin."
            ),
        )
    user = create_user(
        db=db,
        email=user_data.email,
        password=user_data.password,
        full_name=user_data.full_name,
        role=UserRole.buyer,          # always force buyer regardless of payload
        company_name=user_data.company_name,
        company_tax_id=user_data.company_tax_id,
        company_address=user_data.company_address,
        phone=user_data.phone,
    )
    db.commit()
    db.refresh(user)
    
    # Send verification email
    try:
        verification_token = create_verification_token(db, user)
        await send_verification_email(user.email, user.full_name, verification_token)
        db.commit()
    except Exception as e:
        # Log the error but don't fail the signup
        import logging
        logging.getLogger(__name__).error(f"Failed to send verification email to {user.email}: {e}")
    
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
    # Bug #2 fix: gate sellers on their SellerProfile approval status.
    # is_active is only set to False on rejection, but pending sellers must also be blocked.
    if user.role == UserRole.seller:
        profile = db.query(SellerProfile).filter(SellerProfile.user_id == user.id).first()
        if not profile or profile.status == SellerStatus.pending:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Seller account pending approval",
            )
        if profile.status == SellerStatus.rejected:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Seller account rejected: {profile.rejection_reason or ''}",
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


@router.post("/change-password", response_model=MessageResponse)
def change_password(
    payload: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Change password for the currently authenticated user."""
    if not verify_password(payload.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect",
        )
    current_user.hashed_password = get_password_hash(payload.new_password)
    db.commit()
    return MessageResponse(message="Password updated successfully")


@router.get("/verify-email", response_model=EmailVerifyResponse)
def verify_email(token: str = Query(...), db: Session = Depends(get_db)):
    """Verify email address using verification token."""
    user = verify_email_token(db, token)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token",
        )
    
    db.commit()
    return EmailVerifyResponse(
        message="Email verified successfully",
        user=user
    )


@router.post("/resend-verification", response_model=ResendVerificationResponse)
async def resend_verification(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Resend email verification for authenticated user."""
    if current_user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already verified",
        )
    
    # Invalidate existing tokens
    invalidate_user_verification_tokens(db, current_user.id)
    
    # Create new verification token
    verification_token = create_verification_token(db, current_user)
    
    try:
        await send_verification_email(current_user.email, current_user.full_name, verification_token)
        db.commit()
        return ResendVerificationResponse(
            message="Verification email sent successfully"
        )
    except Exception as e:
        db.rollback()
        import logging
        logging.getLogger(__name__).error(f"Failed to send verification email to {current_user.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send verification email. Please try again later.",
        )


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
