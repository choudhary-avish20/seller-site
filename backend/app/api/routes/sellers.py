from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, require_admin
from app.core.auth import create_user, get_user_by_email
from app.db.session import get_db
from app.models.seller import SellerProfile, SellerStatus
from app.models.user import User, UserRole
from app.schemas.auth import (
    SellerApprovalRequest,
    SellerListResponse,
    SellerProfileResponse,
    SellerRegistrationRequest,
    SellerRegistrationResponse,
    UserResponse,
)

router = APIRouter(prefix="/sellers", tags=["sellers"])


@router.post(
    "/register",
    response_model=SellerRegistrationResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_seller(payload: SellerRegistrationRequest, db: Session = Depends(get_db)):
    if get_user_by_email(db, payload.email):
        raise HTTPException(status_code=400, detail="Email already registered")

    user = create_user(
        db=db,
        email=payload.email,
        password=payload.password,
        full_name=payload.full_name,
        role=UserRole.seller,
    )

    sp = payload.seller_profile
    profile = SellerProfile(
        user_id=user.id,
        business_name=sp.business_name,
        tax_id=sp.tax_id,
        business_address=sp.business_address,
        phone=sp.phone,
        status=SellerStatus.pending,
    )
    db.add(profile)
    db.commit()
    db.refresh(user)
    db.refresh(profile)

    return SellerRegistrationResponse(
        user=UserResponse.model_validate(user),
        seller_profile=SellerProfileResponse.model_validate(profile),
    )


@router.get("/me/profile", response_model=SellerProfileResponse)
def get_my_seller_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role != UserRole.seller:
        raise HTTPException(status_code=403, detail="Not a seller account")
    profile = db.query(SellerProfile).filter(SellerProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Seller profile not found")
    return profile


@router.get("/pending", response_model=list[SellerListResponse])
def list_pending_sellers(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    profiles = (
        db.query(SellerProfile)
        .join(User, User.id == SellerProfile.user_id)
        .filter(SellerProfile.status == SellerStatus.pending)
        .order_by(SellerProfile.created_at.desc())
        .all()
    )
    return [
        SellerListResponse(
            id=p.user_id,
            email=p.user.email,
            full_name=p.user.full_name,
            business_name=p.business_name,
            status=p.status,
            created_at=p.created_at,
        )
        for p in profiles
    ]


@router.post("/{seller_id}/approve", response_model=SellerProfileResponse)
def approve_seller(
    seller_id: str,
    payload: SellerApprovalRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    from uuid import UUID

    try:
        uid = UUID(seller_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid seller id")

    profile = db.query(SellerProfile).filter(SellerProfile.user_id == uid).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Seller profile not found")

    if payload.status == SellerStatus.approved:
        profile.status = SellerStatus.approved
        profile.rejection_reason = None
        profile.user.is_active = True
    elif payload.status == SellerStatus.rejected:
        if not payload.rejection_reason:
            raise HTTPException(status_code=400, detail="Rejection reason required")
        profile.status = SellerStatus.rejected
        profile.rejection_reason = payload.rejection_reason
        profile.user.is_active = False
    else:
        raise HTTPException(status_code=400, detail="Invalid status")

    db.commit()
    db.refresh(profile)
    return profile
