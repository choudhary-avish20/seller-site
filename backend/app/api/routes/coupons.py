from datetime import datetime, timezone
from typing import List, Optional, Tuple
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_active_user, require_seller_or_admin
from app.db.session import get_db
from app.models.coupon import Coupon, CouponDiscountType
from app.models.user import User
from app.schemas.coupon import (
    CouponCreate,
    CouponResponse,
    CouponUpdate,
    CouponValidateRequest,
    CouponValidateResponse,
)

router = APIRouter(prefix="/coupons", tags=["coupons"])


def _evaluate_coupon(coupon: Optional[Coupon], order_net: float) -> Tuple[float, Optional[str]]:
    """Returns (discount_amount, error_message). error_message is None when valid."""
    if coupon is None:
        return 0.0, "Coupon code not found"
    if not coupon.active:
        return 0.0, "This coupon is no longer active"
    if coupon.expires_at is not None:
        expires_at = coupon.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at < datetime.now(timezone.utc):
            return 0.0, "This coupon has expired"
    if coupon.max_uses is not None and coupon.used_count >= coupon.max_uses:
        return 0.0, "This coupon has reached its usage limit"
    if coupon.min_order_net is not None and order_net < float(coupon.min_order_net):
        return 0.0, f"Minimum order value for this coupon is {float(coupon.min_order_net):.2f} PLN net"

    if coupon.discount_type == CouponDiscountType.percent:
        discount = round(order_net * float(coupon.discount_value) / 100, 2)
    else:
        discount = round(min(float(coupon.discount_value), order_net), 2)
    return discount, None


def get_valid_coupon(db: Session, code: str, order_net: float) -> Tuple[Optional[Coupon], float, Optional[str]]:
    """Shared lookup used by both the preview endpoint and order creation."""
    coupon = db.query(Coupon).filter(Coupon.code == code.strip().upper()).first()
    discount, error = _evaluate_coupon(coupon, order_net)
    return coupon, discount, error


@router.post("/validate", response_model=CouponValidateResponse)
def validate_coupon(
    payload: CouponValidateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    coupon, discount, error = get_valid_coupon(db, payload.code, payload.order_net)
    if error:
        return CouponValidateResponse(valid=False, code=payload.code.strip().upper(), message=error)
    return CouponValidateResponse(
        valid=True,
        code=coupon.code,
        discount_type=coupon.discount_type,
        discount_value=float(coupon.discount_value),
        min_order_net=float(coupon.min_order_net) if coupon.min_order_net is not None else None,
        discount_amount=discount,
    )


@router.get("", response_model=List[CouponResponse])
def list_coupons(
    db: Session = Depends(get_db),
    _staff: User = Depends(require_seller_or_admin),
):
    return db.query(Coupon).order_by(Coupon.created_at.desc()).all()


@router.post("", response_model=CouponResponse, status_code=status.HTTP_201_CREATED)
def create_coupon(
    payload: CouponCreate,
    db: Session = Depends(get_db),
    _staff: User = Depends(require_seller_or_admin),
):
    if db.query(Coupon).filter(Coupon.code == payload.code).first():
        raise HTTPException(status_code=400, detail=f"Coupon code {payload.code} already exists")
    coupon = Coupon(**payload.model_dump())
    db.add(coupon)
    db.commit()
    db.refresh(coupon)
    return coupon


@router.patch("/{coupon_id}", response_model=CouponResponse)
def update_coupon(
    coupon_id: UUID,
    payload: CouponUpdate,
    db: Session = Depends(get_db),
    _staff: User = Depends(require_seller_or_admin),
):
    coupon = db.query(Coupon).filter(Coupon.id == coupon_id).first()
    if not coupon:
        raise HTTPException(status_code=404, detail="Coupon not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(coupon, field, value)
    db.commit()
    db.refresh(coupon)
    return coupon


@router.delete("/{coupon_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_coupon(
    coupon_id: UUID,
    db: Session = Depends(get_db),
    _staff: User = Depends(require_seller_or_admin),
):
    coupon = db.query(Coupon).filter(Coupon.id == coupon_id).first()
    if not coupon:
        raise HTTPException(status_code=404, detail="Coupon not found")
    db.delete(coupon)
    db.commit()
