from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.api.routes.products import _should_hide_prices, _to_list_response
from app.db.session import get_db
from app.models.product import Product
from app.models.user import User, UserRole
from app.models.wishlist_item import WishlistItem
from app.schemas.wishlist import WishlistItemResponse

router = APIRouter(prefix="/wishlist", tags=["wishlist"])


@router.get("", response_model=List[WishlistItemResponse])
def list_wishlist(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    hide = _should_hide_prices(request, db)
    is_staff = current_user.role in (UserRole.admin, UserRole.seller)
    items = (
        db.query(WishlistItem)
        .filter(WishlistItem.user_id == current_user.id)
        .order_by(WishlistItem.created_at.desc())
        .all()
    )
    result = []
    for item in items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if not product:
            continue  # product was hard-deleted; skip rather than error
        result.append(
            WishlistItemResponse(
                id=item.id,
                product_id=item.product_id,
                created_at=item.created_at,
                product=_to_list_response(product, db, hide_prices=hide, is_staff=is_staff),
            )
        )
    return result


@router.post("/{product_id}", response_model=WishlistItemResponse, status_code=status.HTTP_201_CREATED)
def add_to_wishlist(
    product_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    existing = (
        db.query(WishlistItem)
        .filter(WishlistItem.user_id == current_user.id, WishlistItem.product_id == product_id)
        .first()
    )
    if not existing:
        existing = WishlistItem(user_id=current_user.id, product_id=product_id)
        db.add(existing)
        db.commit()
        db.refresh(existing)

    hide = _should_hide_prices(request, db)
    is_staff = current_user.role in (UserRole.admin, UserRole.seller)
    return WishlistItemResponse(
        id=existing.id,
        product_id=existing.product_id,
        created_at=existing.created_at,
        product=_to_list_response(product, db, hide_prices=hide, is_staff=is_staff),
    )


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_from_wishlist(
    product_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db.query(WishlistItem).filter(
        WishlistItem.user_id == current_user.id, WishlistItem.product_id == product_id
    ).delete()
    db.commit()
    return None
