from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, require_admin, require_role
from app.db.session import get_db
from app.models.category import Category
from app.models.category_request import CategoryRequest, CategoryRequestStatus
from app.models.user import User, UserRole
from app.schemas.category import CategoryRequestCreate, CategoryRequestResponse, CategoryRequestDecision, slugify

router = APIRouter(prefix="/category-requests", tags=["category-requests"])


def _to_response(req: CategoryRequest, db: Session) -> CategoryRequestResponse:
    # enrich with requester_email and parent_name
    from app.models.user import User as UserModel
    requester = db.query(UserModel).filter(UserModel.id == req.requester_id).first()
    parent_name = None
    if req.parent_id:
        parent = db.query(Category).filter(Category.id == req.parent_id).first()
        if parent:
            parent_name = parent.name
    return CategoryRequestResponse(
        id=req.id,
        requester_id=req.requester_id,
        name=req.name,
        slug=req.slug,
        parent_id=req.parent_id,
        description=req.description,
        status=req.status,
        rejection_reason=req.rejection_reason,
        created_category_id=req.created_category_id,
        created_at=req.created_at,
        updated_at=req.updated_at,
        requester_email=requester.email if requester else None,
        parent_name=parent_name,
    )


@router.post("", response_model=CategoryRequestResponse, status_code=status.HTTP_201_CREATED)
def create_category_request(
    payload: CategoryRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # only sellers and admin can request? Spec says seller-facing, but allow seller+admin; buyers shouldn't request categories
    if current_user.role not in (UserRole.seller, UserRole.admin):
        raise HTTPException(status_code=403, detail="Only sellers can request new categories")

    # validate parent exists if provided
    if payload.parent_id:
        parent = db.query(Category).filter(Category.id == payload.parent_id).first()
        if not parent:
            raise HTTPException(status_code=404, detail="Parent category not found")

    slug = payload.slug.strip() if payload.slug else slugify(payload.name)
    if not slug:
        slug = slugify(payload.name)

    # check if slug already exists in categories -> reject request early
    existing_cat = db.query(Category).filter(Category.slug == slug).first()
    if existing_cat:
        raise HTTPException(status_code=400, detail=f"Category with slug '{slug}' already exists")

    # also check pending requests with same slug? allow but warn; we will block duplicate pending?
    pending_same = db.query(CategoryRequest).filter(
        CategoryRequest.slug == slug, CategoryRequest.status == CategoryRequestStatus.pending
    ).first()
    if pending_same:
        raise HTTPException(status_code=400, detail=f"A pending request for slug '{slug}' already exists")

    req = CategoryRequest(
        requester_id=current_user.id,
        name=payload.name.strip(),
        slug=slug,
        parent_id=payload.parent_id,
        description=payload.description.strip() if payload.description else None,
        status=CategoryRequestStatus.pending,
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    return _to_response(req, db)


@router.get("", response_model=List[CategoryRequestResponse])
def list_category_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    status_filter: Optional[CategoryRequestStatus] = Query(None, alias="status"),
    mine: bool = Query(False, description="If true, only own requests (seller)"),
):
    q = db.query(CategoryRequest).order_by(CategoryRequest.created_at.desc())
    if status_filter:
        q = q.filter(CategoryRequest.status == status_filter)

    # role-based filtering
    if current_user.role == UserRole.admin and not mine:
        # admin sees all (optionally filtered)
        pass
    else:
        # seller or admin with mine=true sees only own
        q = q.filter(CategoryRequest.requester_id == current_user.id)

    reqs = q.all()
    return [_to_response(r, db) for r in reqs]


@router.get("/{request_id}", response_model=CategoryRequestResponse)
def get_category_request(
    request_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    req = db.query(CategoryRequest).filter(CategoryRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    if current_user.role != UserRole.admin and req.requester_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this request")
    return _to_response(req, db)


@router.post("/{request_id}/decision", response_model=CategoryRequestResponse)
def decide_category_request(
    request_id: UUID,
    payload: CategoryRequestDecision,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    req = db.query(CategoryRequest).filter(CategoryRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    if req.status != CategoryRequestStatus.pending:
        raise HTTPException(status_code=400, detail=f"Request already {req.status.value}")

    if payload.action == "approve":
        # double-check slug still unique
        if db.query(Category).filter(Category.slug == req.slug).first():
            raise HTTPException(status_code=400, detail=f"Slug '{req.slug}' already exists as category")
        # double-check parent still exists
        if req.parent_id and not db.query(Category).filter(Category.id == req.parent_id).first():
            raise HTTPException(status_code=404, detail="Parent category no longer exists")

        new_cat = Category(
            name=req.name,
            slug=req.slug,
            parent_id=req.parent_id,
            is_active=True,
        )
        db.add(new_cat)
        db.flush()  # get id
        req.status = CategoryRequestStatus.approved
        req.created_category_id = new_cat.id
        req.rejection_reason = None
        db.commit()
        db.refresh(req)
        return _to_response(req, db)
    elif payload.action == "reject":
        if not payload.rejection_reason or not payload.rejection_reason.strip():
            raise HTTPException(status_code=400, detail="Rejection reason is required")
        req.status = CategoryRequestStatus.rejected
        req.rejection_reason = payload.rejection_reason.strip()
        db.commit()
        db.refresh(req)
        return _to_response(req, db)
    else:
        raise HTTPException(status_code=400, detail="Invalid action")
