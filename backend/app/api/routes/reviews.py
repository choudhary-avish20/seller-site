from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.api.routes.products import _get_optional_user
from app.db.session import get_db
from app.models.product import Product
from app.models.review import Review
from app.models.user import User, UserRole
from app.schemas.review import ReviewCreate, ReviewResponse

router = APIRouter(prefix="/reviews", tags=["reviews"])


def _to_response(review: Review, db: Session, viewer_id) -> ReviewResponse:
    reviewer = db.query(User).filter(User.id == review.user_id).first()
    name = "Klient"
    if reviewer:
        name = reviewer.company_name or reviewer.full_name
    return ReviewResponse(
        id=review.id,
        product_id=review.product_id,
        rating=review.rating,
        comment=review.comment,
        created_at=review.created_at,
        reviewer_name=name,
        is_own=(viewer_id is not None and review.user_id == viewer_id),
    )


@router.get("/product/{product_id}", response_model=List[ReviewResponse])
def list_reviews(product_id: UUID, request: Request, db: Session = Depends(get_db)):
    viewer = _get_optional_user(request, db)
    reviews = (
        db.query(Review)
        .filter(Review.product_id == product_id)
        .order_by(Review.created_at.desc())
        .all()
    )
    return [_to_response(r, db, viewer.id if viewer else None) for r in reviews]


@router.post("/product/{product_id}", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
def upsert_review(
    product_id: UUID,
    payload: ReviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != UserRole.buyer:
        raise HTTPException(status_code=403, detail="Tylko kupujący mogą dodawać recenzje")
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    review = (
        db.query(Review)
        .filter(Review.product_id == product_id, Review.user_id == current_user.id)
        .first()
    )
    if review:
        review.rating = payload.rating
        review.comment = payload.comment
    else:
        review = Review(product_id=product_id, user_id=current_user.id, rating=payload.rating, comment=payload.comment)
        db.add(review)
    db.commit()
    db.refresh(review)
    return _to_response(review, db, current_user.id)


@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_review(
    review_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    if review.user_id != current_user.id and current_user.role not in (UserRole.admin, UserRole.seller):
        raise HTTPException(status_code=403, detail="Not authorized")
    db.delete(review)
    db.commit()
    return None
