from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.api.dependencies import get_current_user, require_admin
from app.db.session import get_db
from app.core.auth import (
    create_user,
    create_seller_profile,
    get_seller_profile,
    get_pending_sellers,
    approve_seller,
    reject_seller,
    get_user_by_email,
)
from app.models.user import User, UserRole
from app.models.seller import SellerProfile, SellerStatus
from app.schemas.auth import (
    SellerRegistrationRequest,
    SellerRegistrationResponse,
    SellerProfileResponse,
    SellerApprovalRequest,
    SellerListResponse,
    UserResponse,
)


router = APIRouter(prefix="/sellers", tags=["sellers"])


@router.post("/register", response_model=SellerRegistrationResponse, status_code=status.HTTP_201_CREATED)
def register_seller(seller_data: SellerRegistrationRequest, db: Session = Depends(get_db)):
    if get_user_by_email(db, seller_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    user = create_user(
        db=db,
        email=seller_data.email,
        password=seller_data.password,
        full_name=seller_data.full_name,
        role=UserRole.seller,
    )
    seller_profile = create_seller_profile(
        db=db,
        user_id=user.id,
        business_name=seller_data.seller_profile.business_name,
        tax_id=seller_data.seller_profile.tax_id,
        business_address=seller_data.seller_profile.business_address,
        phone=seller_data.seller_profile.phone,
    )
    db.commit()
    db.refresh(user)
    db.refresh(seller_profile)
    return SellerRegistrationResponse(user=user, seller_profile=seller_profile)


@router.get("/me/profile", response_model=SellerProfileResponse)
def get_my_seller_profile(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != UserRole.seller:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only sellers have profiles",
        )
    seller_profile = get_seller_profile(db, current_user.id)
    if not seller_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Seller profile not found",
        )
    return seller_profile


@router.get("/pending", response_model=list[SellerListResponse])
def list_pending_sellers(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    pending_sellers = get_pending_sellers(db)
    result = []
    for sp in pending_sellers:
        user = sp.user
        result.append(
            SellerListResponse(
                id=str(sp.id),
                email=user.email,
                full_name=user.full_name,
                business_name=sp.business_name,
                status=sp.status,
                created_at=sp.created_at,
            )
        )
    return result


@router.post("/{seller_id}/approve", response_model=SellerProfileResponse)
def approve_seller_registration(
    seller_id: UUID,
    approval: SellerApprovalRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    if approval.status == SellerStatus.approved:
        seller = approve_seller(db, seller_id, current_user.id)
    elif approval.status == SellerStatus.rejected:
        if not approval.rejection_reason:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Rejection reason is required when rejecting a seller",
            )
        seller = reject_seller(db, seller_id, current_user.id, approval.rejection_reason)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid status. Must be 'approved' or 'rejected'",
        )
    if not seller:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Seller not found",
        )
    db.commit()
    db.refresh(seller)
    return seller


@router.get("/{seller_id}", response_model=SellerProfileResponse)
def get_seller(
    seller_id: UUID,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    seller = db.query(SellerProfile).filter(SellerProfile.id == seller_id).first()
    if not seller:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Seller not found",
        )
    return seller